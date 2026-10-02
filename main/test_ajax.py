import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from main.forms import ProjectForm
from main.models import Project
from main.project_queries import PUBLIC_PROJECT_FIELDS
from main.views import get_projects_json


def project_payload(**overrides):
    data = {
        "title": "AJAX portfolio project",
        "description": "A project added from the modal.",
        "tech_stack": "Django, JavaScript",
        "project_url": "",
        "project_image_url": "",
    }
    data.update(overrides)
    return data


class CreateProjectAjaxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(username="ajax_admin")
        cls.user = User.objects.create_user(username="ajax_user")
        cls.staff = User.objects.create_user(username="ajax_staff", is_staff=True)
        cls.editor = User.objects.create_user(username="ajax_editor")
        cls.editor.groups.add(Group.objects.get_or_create(name="Editor")[0])

    def setUp(self):
        self.url = reverse("main:create_project_ajax")

    def test_only_superusers_can_create_and_denials_are_json_without_redirects(self):
        count = Project.objects.count()
        for user in (None, self.user, self.staff, self.editor):
            with self.subTest(user=user):
                if user is None:
                    self.client.logout()
                else:
                    self.client.force_login(user)
                response = self.client.post(self.url, project_payload())
                self.assertEqual(response.status_code, 403)
                self.assertNotIn("Location", response)
                self.assertEqual(
                    response.json(),
                    {"message": "Hanya pemilik portofolio yang dapat menambahkan proyek."},
                )
                self.assertEqual(Project.objects.count(), count)

    def test_non_post_methods_are_rejected_without_creating_data(self):
        self.client.force_login(self.admin)
        count = Project.objects.count()
        for method in ("get", "put", "patch", "delete", "head"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], "POST")
        self.assertEqual(Project.objects.count(), count)

    def test_valid_submission_creates_one_project_and_returns_its_id(self):
        self.client.force_login(self.admin)
        count = Project.objects.count()
        data = project_payload(project_url="https://example.com/demo")
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Proyek berhasil ditambahkan.")
        self.assertEqual(Project.objects.count(), count + 1)
        saved = Project.objects.get(pk=response.json()["pk"])
        for field, value in data.items():
            self.assertEqual(getattr(saved, field), value)

    def test_invalid_fields_return_structured_errors_without_saving(self):
        self.client.force_login(self.admin)
        count = Project.objects.count()
        for field, value in (
            ("title", "   "),
            ("title", "a" * 256),
            ("description", ""),
            ("tech_stack", "a" * 256),
            ("project_url", "javascript:alert(1)"),
            ("project_image_url", "data:image/svg+xml,bad"),
        ):
            with self.subTest(field=field, value=value):
                response = self.client.post(self.url, project_payload(**{field: value}))
                self.assertEqual(response.status_code, 400)
                errors = response.json()["errors"][field]
                self.assertTrue(errors[0]["message"])
                self.assertTrue(errors[0]["code"])
                self.assertEqual(Project.objects.count(), count)

    def test_empty_request_reports_all_required_fields(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()["errors"]), {"title", "description", "tech_stack"})

    def test_csrf_token_is_required_and_a_valid_header_allows_creation(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        count = Project.objects.count()
        self.assertEqual(client.post(self.url, project_payload()).status_code, 403)
        self.assertEqual(Project.objects.count(), count)

        client.get(reverse("main:show_projects"))
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(self.url, project_payload(), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.count(), count + 1)

    def test_anonymous_request_with_csrf_gets_json_permission_error(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("main:login"))
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(self.url, project_payload(), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 403)
        self.assertIn("message", response.json())


class ProjectSanitizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="sanitization_admin")

    def test_all_text_fields_strip_tags_and_surrounding_whitespace(self):
        form = ProjectForm(project_payload(
            title="  <b>Portfolio</b> website  ",
            description="  A <em>Django</em> application.  ",
            tech_stack="  <span>Python</span>, Django  ",
        ))
        self.assertTrue(form.is_valid(), form.errors)
        project = form.save()
        project.refresh_from_db()
        self.assertEqual(project.title, "Portfolio website")
        self.assertEqual(project.description, "A Django application.")
        self.assertEqual(project.tech_stack, "Python, Django")

    def test_tags_cannot_bypass_required_text_fields(self):
        for field in ("title", "description", "tech_stack"):
            with self.subTest(field=field):
                form = ProjectForm(project_payload(**{field: '<img src="x" onerror="alert(1)">'}))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_ajax_and_classic_create_and_update_share_sanitization(self):
        self.client.force_login(self.admin)
        for route in ("create_project_ajax", "create_project"):
            with self.subTest(route=route):
                response = self.client.post(
                    reverse(f"main:{route}"),
                    project_payload(title=f"<b>{route}</b>"),
                )
                self.assertIn(response.status_code, (201, 302))
                saved = Project.objects.get(title=route)
                response = self.client.post(
                    reverse("main:update_project", args=[saved.pk]),
                    project_payload(title=f"<i>Updated {route}</i>"),
                )
                self.assertEqual(response.status_code, 302)
                saved.refresh_from_db()
                self.assertEqual(saved.title, f"Updated {route}")

    def test_tag_only_title_returns_validation_message_to_ajax_client(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("main:create_project_ajax"),
            project_payload(title='<img src="x" onerror="alert(1)">'),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["errors"]["title"][0]["message"],
            "Nama proyek tidak boleh hanya berisi tag HTML.",
        )


class ProjectAjaxDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Project.objects.all().delete()
        User = get_user_model()
        cls.first_user = User.objects.create_user(username="private_star_account")
        cls.second_user = User.objects.create_user(username="other_private_account")
        cls.viewer = User.objects.create_user(username="non_starring_viewer")
        cls.project = Project.objects.create(**project_payload(title="FocusBuddy project"))
        cls.other_project = Project.objects.create(**project_payload(title="Other project"))
        cls.project.starred_by.add(cls.first_user, cls.second_user)

    def test_public_json_contains_counts_and_only_current_viewer_star_status(self):
        for user, is_starred in ((None, False), (self.first_user, True), (self.viewer, False)):
            with self.subTest(user=user):
                if user is None:
                    self.client.logout()
                else:
                    self.client.force_login(user)
                response = self.client.get(reverse("main:get_projects_json"))
                rows = {row["pk"]: row for row in response.json()}
                project = rows[str(self.project.pk)]
                self.assertEqual(project["model"], "main.project")
                self.assertEqual(
                    set(project["fields"]),
                    set(PUBLIC_PROJECT_FIELDS) | {"star_count", "is_starred"},
                )
                self.assertEqual(project["fields"]["star_count"], 2)
                self.assertIs(project["fields"]["is_starred"], is_starred)
                self.assertEqual(rows[str(self.other_project.pk)]["fields"]["star_count"], 0)
                self.assertNotContains(response, self.first_user.username)
                self.assertNotContains(response, self.second_user.username)
                self.assertNotContains(response, '"starred_by"')

    def test_json_search_is_trimmed_and_case_insensitive(self):
        response = self.client.get(reverse("main:get_projects_json"), {"title": "  fOcUsBuDdY  "})
        self.assertEqual([row["pk"] for row in response.json()], [str(self.project.pk)])
        self.assertEqual(response.json()[0]["fields"]["star_count"], 2)
        self.assertEqual(
            self.client.get(reverse("main:get_projects_json"), {"title": "no match"}).json(),
            [],
        )

    def test_json_reflects_star_and_unstar_for_the_logged_in_user(self):
        self.client.force_login(self.viewer)
        star_url = reverse("main:toggle_star", args=[self.project.pk])
        json_url = reverse("main:get_projects_json")
        for count, is_starred in ((3, True), (2, False)):
            with self.subTest(is_starred=is_starred):
                self.assertEqual(self.client.post(star_url).status_code, 302)
                rows = {row["pk"]: row["fields"] for row in self.client.get(json_url).json()}
                self.assertEqual(rows[str(self.project.pk)]["star_count"], count)
                self.assertIs(rows[str(self.project.pk)]["is_starred"], is_starred)

    def test_empty_database_returns_an_empty_json_array(self):
        Project.objects.all().delete()
        response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), [])

    def test_star_json_requires_one_query_for_many_projects(self):
        Project.objects.bulk_create([
            Project(**project_payload(title=f"Additional project {number}"))
            for number in range(20)
        ])
        for user in (AnonymousUser(), self.first_user):
            with self.subTest(user=user):
                request = RequestFactory().get(reverse("main:get_projects_json"))
                request.user = user
                with self.assertNumQueries(1):
                    response = get_projects_json(request)
                self.assertEqual(len(json.loads(response.content)), 22)

    def test_projects_page_is_a_shell_and_does_not_query_project_records(self):
        with self.assertNumQueries(0):
            response = self.client.get(reverse("main:show_projects"), {"title": "  FocusBuddy  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["title_query"], "FocusBuddy")
        self.assertIsInstance(response.context["form"], ProjectForm)
        self.assertFalse(response.context["form"].is_bound)
        self.assertNotIn("project_list", response.context)
        self.assertNotContains(response, self.project.description)
