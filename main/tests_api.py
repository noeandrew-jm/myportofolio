"""Project API contracts, role permissions, validation, and real session CSRF."""

import uuid

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Project
from main.serializers import ProjectSerializer


class ProjectAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # These accounts exist only in Django's isolated test database.
        cls.password = "api-test-password"
        cls.owner = User.objects.create_superuser(
            username="api-owner", password=cls.password, email="owner@example.com",
        )
        cls.visitor = User.objects.create_user(
            username="api-visitor", password=cls.password, email="private@example.com",
            first_name="Private", last_name="Account",
        )
        cls.editor = User.objects.create_user(username="api-editor", password=cls.password)
        cls.editor.groups.add(Group.objects.get_or_create(name="Editor")[0])
        cls.project = Project.objects.create(
            title="Portfolio", description="My website", tech_stack="Django",
        )

    def setUp(self):
        self.list_url = reverse("api:project-list")
        self.detail_url = reverse("api:project-detail", args=[self.project.id])
        self.star_url = reverse("api:project-star", args=[self.project.id])
        self.payload = {
            "title": "New project", "description": "A useful app", "tech_stack": "Python",
            "project_url": "https://example.com/", "project_image_url": "",
        }

    def session_client(self, user):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username=user.username, password=self.password))
        return client

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = response.data[0]
        self.assertEqual(record["id"], str(self.project.id))
        self.assertFalse(record["is_starred"])
        self.assertEqual(set(record), {
            "id", "title", "description", "tech_stack", "project_url",
            "project_image_url", "star_count", "is_starred", "starred_by_names",
        })
        detail = self.client.get(self.detail_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data, record)

    def test_search_and_empty_results(self):
        Project.objects.create(title="Alpha", description="First", tech_stack="Python")
        response = self.client.get(self.list_url, {"title": "  PORT  "})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data], [str(self.project.id)])
        response = self.client.get(self.list_url, {"title": "not-found"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        response = self.client.get(self.list_url)
        self.assertEqual([row["title"] for row in response.data], ["Alpha", "Portfolio"])

    def test_missing_project(self):
        missing_id = uuid.uuid4()
        detail_url = reverse("api:project-detail", args=[missing_id])
        star_url = reverse("api:project-star", args=[missing_id])
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.client.force_authenticate(user=self.owner)
        for method in ("get", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(detail_url, {}, format="json")
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(star_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            for method, url, payload in (
                ("post", self.list_url, self.payload),
                ("patch", self.detail_url, {"title": "Changed"}),
                ("put", self.detail_url, self.payload),
                ("delete", self.detail_url, {}),
            ):
                with self.subTest(user=user, method=method):
                    response = getattr(self.client, method)(url, payload, format="json")
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")

    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(pk=response.data["id"])
        for field, value in self.payload.items():
            self.assertEqual(getattr(project, field), value)
        self.assertEqual(Project.objects.count(), 2)

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        invalid_inputs = [
            (field, value)
            for field in ("title", "description", "tech_stack")
            for value in ("   ", '<img src="x" onerror="alert(1)">')
        ] + [
            (field, value)
            for field in ("project_url", "project_image_url")
            for value in (
                "javascript:alert(1)", "data:text/html,<script>alert(1)</script>",
                "ftp://example.com/project", "ftps://example.com/project", "not-a-url",
            )
        ]
        for field, value in invalid_inputs:
            for method, url, payload in (
                ("post", self.list_url, {**self.payload, field: value}),
                ("patch", self.detail_url, {field: value}),
            ):
                with self.subTest(field=field, value=value, method=method):
                    response = getattr(self.client, method)(url, payload, format="json")
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertIn(field, response.data)
        self.assertEqual(Project.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")
        self.assertEqual(self.project.description, "My website")
        self.assertEqual(self.project.tech_stack, "Django")
        self.assertEqual(self.project.project_url, "")
        self.assertEqual(self.project.project_image_url, "")

    def test_text_is_sanitized_and_web_urls_preserve_query_parameters(self):
        self.client.force_authenticate(user=self.owner)
        payload = {
            "title": "  <b>Portfolio</b> website  ",
            "description": "  A <em>Django</em> application.  ",
            "tech_stack": "  <span>Python</span>, Django  ",
            "project_url": "https://example.com/project?source=portfolio&mode=demo",
            "project_image_url": "http://example.com/image.png?width=800&height=600",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(pk=response.data["id"])
        self.assertEqual(project.title, "Portfolio website")
        self.assertEqual(project.description, "A Django application.")
        self.assertEqual(project.tech_stack, "Python, Django")
        self.assertEqual(project.project_url, payload["project_url"])
        self.assertEqual(project.project_image_url, payload["project_image_url"])

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Changed")
        self.assertEqual(self.project.description, "My website")
        response = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)
        self.assertIn("tech_stack", response.data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Changed")
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        for field, value in self.payload.items():
            self.assertEqual(getattr(self.project, field), value)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.project.starred_by.count(), 0)
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        self.assertEqual(response.data["starred_by_names"], self.visitor.username)
        self.assertEqual(list(self.project.starred_by.all()), [self.visitor])
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)
        self.assertEqual(response.data["starred_by_names"], "")
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_star_always_uses_current_user_and_preserves_other_stars(self):
        self.project.starred_by.add(self.owner)
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url, {
            "user": self.editor.pk, "user_id": self.editor.pk,
            "starred_by": [self.editor.pk], "star_count": 99,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["star_count"], 2)
        self.assertEqual(set(self.project.starred_by.all()), {self.owner, self.visitor})
        self.client.post(self.star_url)
        self.assertEqual(list(self.project.starred_by.all()), [self.owner])

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        forged_id = uuid.uuid4()
        forged = {
            "id": str(forged_id), "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.visitor.id],
        }
        response = self.client.post(self.list_url, {**self.payload, **forged}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], str(forged_id))
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "")
        self.assertEqual(Project.objects.get(pk=response.data["id"]).starred_by.count(), 0)
        self.project.starred_by.add(self.visitor)
        response = self.client.patch(self.detail_url, forged, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.project.pk))
        self.assertEqual(response.data["star_count"], 1)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], self.visitor.username)
        self.assertEqual(list(self.project.starred_by.all()), [self.visitor])

    def test_staff_status_alone_cannot_manage_projects(self):
        self.visitor.is_staff = True
        self.visitor.save(update_fields=["is_staff"])
        self.client.force_authenticate(user=self.visitor)
        for method, url in (
            ("post", self.list_url), ("put", self.detail_url),
            ("patch", self.detail_url), ("delete", self.detail_url),
        ):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, self.payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")

    def test_editor_can_update_but_cannot_create_or_delete_chosen_projects(self):
        # Projects is this portfolio's chosen assignment section, so its existing
        # Editor role must also apply to API updates (the tutorial's final step).
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"title": "Editor update"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Editor update")
        self.assertEqual(self.project.description, "My website")
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, self.payload["title"])
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        for method, url in (
            ("delete", self.list_url), ("put", self.list_url),
            ("patch", self.list_url), ("post", self.detail_url),
            ("get", self.star_url), ("put", self.star_url),
            ("delete", self.star_url),
        ):
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, {}, format="json")
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_safe_methods_do_not_change_projects_or_stars(self):
        self.project.starred_by.add(self.visitor)
        for user in (None, self.visitor, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            for url in (self.list_url, self.detail_url):
                for method in ("get", "head", "options"):
                    with self.subTest(user=user, method=method, url=url):
                        response = getattr(self.client, method)(url)
                        self.assertEqual(response.status_code, status.HTTP_200_OK)
                        if method == "head":
                            self.assertEqual(response.content, b"")
        self.project.refresh_from_db()
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(self.project.title, "Portfolio")
        self.assertEqual(list(self.project.starred_by.all()), [self.visitor])

    def test_session_write_without_csrf_is_rejected(self):
        client = self.session_client(self.owner)
        for method, url in (
            ("post", self.list_url), ("put", self.detail_url),
            ("patch", self.detail_url), ("delete", self.detail_url),
            ("post", self.star_url),
        ):
            with self.subTest(method=method, url=url):
                response = getattr(client, method)(url, self.payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertIn("CSRF", str(response.data["detail"]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_session_write_with_csrf_succeeds(self):
        client = self.session_client(self.owner)
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        headers = {"format": "json", "HTTP_X_CSRFTOKEN": token}
        response = client.post(self.list_url, self.payload, **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = client.patch(self.detail_url, {"title": "Session update"}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Session update")
        response = client.put(self.detail_url, self.payload, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = client.post(self.star_url, {}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
        response = client.delete(self.detail_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_projects_page_reissues_csrf_for_member_with_existing_session(self):
        client = self.session_client(self.visitor)
        client.cookies.pop(settings.CSRF_COOKIE_NAME, None)
        page = client.get(reverse("main:show_projects"))
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        self.assertNotContains(page, 'id="add-project-modal"')
        self.assertIn(settings.CSRF_COOKIE_NAME, client.cookies)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(self.star_url, {}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(list(self.project.starred_by.all()), [self.visitor])

    def test_incorrect_csrf_token_and_untrusted_origin_are_rejected(self):
        client = self.session_client(self.owner)
        client.get(self.list_url, HTTP_ACCEPT="text/html")
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        for headers in (
            {"HTTP_X_CSRFTOKEN": "invalid-token"},
            {"HTTP_X_CSRFTOKEN": token, "HTTP_ORIGIN": "https://attacker.example"},
        ):
            with self.subTest(headers=headers):
                response = client.post(self.list_url, self.payload, format="json", **headers)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), 1)

    def test_star_metadata_is_viewer_specific_without_private_account_fields(self):
        self.project.starred_by.add(self.visitor)
        for user, expected in ((None, False), (self.owner, False), (self.visitor, True)):
            self.client.force_authenticate(user=user)
            for url in (self.list_url, self.detail_url):
                with self.subTest(user=user, url=url):
                    response = self.client.get(url)
                    record = response.data[0] if url == self.list_url else response.data
                    self.assertEqual(record["star_count"], 1)
                    self.assertEqual(record["is_starred"], expected)
                    self.assertEqual(record["starred_by_names"], self.visitor.username)
                    for field in ("starred_by", "email", "password", "first_name", "last_name"):
                        self.assertNotIn(field, record)
                    body = response.content.decode()
                    self.assertNotIn(self.visitor.email, body)
                    self.assertNotIn(self.visitor.password, body)

    def test_listing_prefetches_stars_instead_of_querying_per_project(self):
        for index in range(5):
            project = Project.objects.create(
                title=f"Extra project {index}", description="Query coverage", tech_stack="Django",
            )
            project.starred_by.add(self.visitor)
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            with self.subTest(user=user), self.assertNumQueries(2):
                response = self.client.get(self.list_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(response.data), 6)

    def test_invalid_json_returns_400_without_creating_project(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, '{"title":', content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Project.objects.count(), 1)


class ProjectSerializerTests(SimpleTestCase):
    def test_optional_urls_and_required_fields_match_shell_example(self):
        candidate = ProjectSerializer(data={
            "title": "Portfolio", "description": "My website", "tech_stack": "Django",
        })
        self.assertTrue(candidate.is_valid(), candidate.errors)
        self.assertEqual(candidate.validated_data["title"], "Portfolio")
        invalid = ProjectSerializer(data={"title": ""})
        self.assertFalse(invalid.is_valid())
        self.assertEqual(set(invalid.errors), {"title", "description", "tech_stack"})

    def test_computed_values_are_not_validated_input(self):
        candidate = ProjectSerializer(data={
            "title": "Portfolio", "description": "My website", "tech_stack": "Django",
            "project_url": "", "project_image_url": "", "id": str(uuid.uuid4()),
            "star_count": 999, "is_starred": True, "starred_by_names": "forged",
            "starred_by": [123],
        })
        self.assertTrue(candidate.is_valid(), candidate.errors)
        self.assertEqual(set(candidate.validated_data), {
            "title", "description", "tech_stack", "project_url", "project_image_url",
        })
