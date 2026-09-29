import json
import uuid
from unittest.mock import patch
from xml.etree import ElementTree

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.html import escape

from main.forms import ProjectForm
from main.models import Project


def project_data(**overrides):
    data = {
        "title": "Portfolio website",
        "description": "A Django portfolio built for PBP.",
        "tech_stack": "Django, Python, HTML, CSS",
        "project_url": "",
        "project_image_url": "",
    }
    data.update(overrides)
    return data


class ProjectUpdateTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(username="project_update_admin")
        self.client.force_login(self.admin)
        self.project = Project.objects.create(**project_data(title="Original project"))
        self.url = reverse("main:update_project", args=[self.project.pk])

    def test_edit_form_uses_existing_instance_and_shared_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertEqual(response.context["form"].instance.pk, self.project.pk)
        self.assertContains(response, 'value="Original project"')
        self.assertContains(response, f'action="{self.url}"')
        self.assertContains(response, "Simpan Perubahan")
        detail = self.client.get(reverse("main:project_detail", args=[self.project.pk]))
        self.assertContains(detail, f'href="{self.url}"')

    def test_update_changes_same_record_and_serialized_listing(self):
        count = Project.objects.count()
        data = project_data(title="Updated project", description="Revised description", tech_stack="Python, Django")
        response = self.client.post(self.url, data, follow=True)
        self.assertRedirects(response, reverse("main:show_projects"))
        self.project.refresh_from_db()
        self.assertEqual(Project.objects.count(), count)
        for field, value in data.items():
            self.assertEqual(getattr(self.project, field), value)
        self.assertContains(response, "Proyek berhasil diperbarui!")
        record = next(row for row in self.client.get(reverse("main:get_projects_json")).json() if row["pk"] == str(self.project.pk))
        self.assertEqual(record["fields"]["title"], "Updated project")
        self.assertEqual(record["fields"]["description"], "Revised description")

    def test_invalid_update_preserves_saved_record_and_bound_input(self):
        response = self.client.post(self.url, project_data(title="Unsaved title", project_url="invalid URL"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].is_bound)
        self.assertIn("project_url", response.context["form"].errors)
        self.assertContains(response, 'value="Unsaved title"')
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Original project")

    def test_unknown_project_and_unsupported_methods(self):
        missing = reverse("main:update_project", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(missing).status_code, 404)
        self.assertEqual(self.client.post(missing, project_data()).status_code, 404)
        self.assertEqual(self.client.delete(self.url).status_code, 405)

    def test_edit_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url, project_data()).status_code, 403)
        client.get(self.url)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(self.url, project_data(title="CSRF verified", csrfmiddlewaretoken=token))
        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "CSRF verified")


class ProjectDetailUrlTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(**project_data())
        self.url = reverse("main:project_detail", args=[self.project.pk])

    def test_detail_preserves_http_and_https_urls_with_escaped_attributes(self):
        self.project.project_url = "https://example.com/demo?source=portfolio&mode=preview"
        self.project.project_image_url = "http://example.com/image.png?width=800&height=600"
        self.project.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{escape(self.project.project_url)}"')
        self.assertContains(response, f'src="{escape(self.project.project_image_url)}"')
        self.assertContains(response, "Lihat Proyek")

    def test_detail_omits_unsafe_legacy_urls_without_changing_saved_data(self):
        # Direct database writes bypass ProjectForm, as can older imported data.
        for value in (
            "javascript:alert(1)",
            "JaVaScRiPt:alert(1)",
            "java\nscript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "ftp://example.com/project",
            "//example.com/project",
            "https://[broken",
        ):
            with self.subTest(value=value):
                self.project.project_url = value
                self.project.project_image_url = value
                self.project.save()

                response = self.client.get(self.url)

                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "Lihat Proyek")
                self.assertNotContains(response, 'class="project-image"')
                self.project.refresh_from_db()
                self.assertEqual(self.project.project_url, value)
                self.assertEqual(self.project.project_image_url, value)


class ProjectFormTests(TestCase):
    def test_required_fields_and_optional_urls(self):
        form = ProjectForm(project_data())

        self.assertTrue(form.is_valid(), form.errors)
        project = form.save()
        project.refresh_from_db()
        self.assertIsInstance(project.pk, uuid.UUID)
        self.assertEqual(str(project), "Portfolio website")
        self.assertEqual(project.project_url, "")
        self.assertEqual(project.project_image_url, "")

    def test_blank_required_fields_are_rejected(self):
        for field in ("title", "description", "tech_stack"):
            with self.subTest(field=field):
                form = ProjectForm(project_data(**{field: "   "}))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_optional_urls_are_validated_when_supplied(self):
        for field in ("project_url", "project_image_url"):
            for value in ("not a valid URL", "javascript:alert(1)"):
                with self.subTest(field=field, value=value):
                    form = ProjectForm(project_data(**{field: value}))
                    self.assertFalse(form.is_valid())
                    self.assertIn(field, form.errors)

    def test_model_length_limits_are_enforced_by_form(self):
        for field, value in (
            ("title", "a" * 256),
            ("tech_stack", "a" * 256),
            ("project_url", "https://example.com/" + "a" * 200),
            ("project_image_url", "https://example.com/" + "a" * 500),
        ):
            with self.subTest(field=field):
                form = ProjectForm(project_data(**{field: value}))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_image_url_longer_than_default_url_limit_is_supported(self):
        image_url = "https://example.com/" + "a" * 250
        form = ProjectForm(project_data(project_image_url=image_url))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().project_image_url, image_url)


class ProjectPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="project_admin")
        Project.objects.all().delete()
        cls.project = Project.objects.create(
            **project_data(
                title="FocusBuddy planner",
                project_url="https://example.com/project?source=portfolio&mode=demo",
                project_image_url="https://example.com/focusbuddy.png",
            )
        )
        cls.other_project = Project.objects.create(
            **project_data(title="Personal portfolio", description="A second project.")
        )

    def test_list_and_form_share_layout_and_owner(self):
        for route, template in (
            ("show_projects", "project.html"),
            ("create_project", "projects_form.html"),
        ):
            with self.subTest(route=route):
                if route == "create_project":
                    self.client.force_login(self.admin)
                response = self.client.get(reverse(f"main:{route}"))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                self.assertTemplateUsed(response, "base.html")
                self.assertEqual(response.context["name"], "Noe Andrew")
                self.assertEqual(response.context["active_page"], "projects")
                self.assertContains(response, "<title>", count=1)
                self.assertContains(response, 'class="site-header"', count=1)
                self.assertContains(response, 'class="site-footer"', count=1)
                self.assertContains(response, 'aria-current="page"', count=1)
                self.assertContains(response, f'href="{reverse("main:show_projects")}"')

    def test_list_returns_ajax_shell_and_public_api_provides_card_data(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertNotIn("project_list", response.context)
        self.assertIsInstance(response.context["form"], ProjectForm)
        self.assertFalse(response.context["form"].is_bound)
        for element_id in ("project-search-form", "search-input", "loading", "error", "empty", "grid", "project-cards"):
            self.assertContains(response, f'id="{element_id}"', count=1)
        payload = self.client.get(reverse("main:get_projects_json")).json()
        records = {item["pk"]: item["fields"] for item in payload}
        self.assertEqual(set(records), {str(self.project.pk), str(self.other_project.pk)})
        for project in (self.project, self.other_project):
            self.assertNotContains(response, project.title)
            for field in project_data():
                self.assertEqual(records[str(project.pk)][field], getattr(project, field))
        self.assertNotContains(response, 'id="add-project-modal"')

    def test_get_form_is_unbound_and_does_not_create_data(self):
        self.client.force_login(self.admin)
        count = Project.objects.count()
        response = self.client.get(reverse("main:create_project"))

        self.assertFalse(response.context["form"].is_bound)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertEqual(Project.objects.count(), count)

    def test_valid_post_saves_and_redirects_with_visible_success_message(self):
        self.client.force_login(self.admin)
        data = project_data(
            title="New project via form",
            project_url="https://example.com/new",
            project_image_url="https://drive.google.com/thumbnail?id=example&sz=w1000",
        )
        response = self.client.post(reverse("main:create_project"), data, follow=True)

        self.assertRedirects(response, reverse("main:show_projects"))
        saved = Project.objects.get(title=data["title"])
        for field, value in data.items():
            self.assertEqual(getattr(saved, field), value)
        self.assertContains(response, "Proyek baru berhasil ditambahkan!")
        payload = self.client.get(reverse("main:get_projects_json")).json()
        self.assertIn(str(saved.pk), {item["pk"] for item in payload})

    def test_post_can_create_without_optional_urls(self):
        self.client.force_login(self.admin)
        data = project_data(title="Text only project")
        data.pop("project_url")
        data.pop("project_image_url")
        response = self.client.post(reverse("main:create_project"), data)

        self.assertRedirects(response, reverse("main:show_projects"))
        saved = Project.objects.get(title=data["title"])
        self.assertEqual(saved.project_url, "")
        self.assertEqual(saved.project_image_url, "")

    def test_empty_post_returns_bound_errors_and_does_not_save(self):
        self.client.force_login(self.admin)
        count = Project.objects.count()
        response = self.client.post(reverse("main:create_project"), {})

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.is_bound)
        for field in ("title", "description", "tech_stack"):
            self.assertIn(field, form.errors)
            self.assertContains(response, escape(form.errors[field][0]))
        self.assertEqual(Project.objects.count(), count)

    def test_invalid_post_preserves_input_and_shows_errors(self):
        self.client.force_login(self.admin)
        count = Project.objects.count()
        data = project_data(title="Keep this title", project_url="invalid URL")
        response = self.client.post(reverse("main:create_project"), data)

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.is_bound)
        self.assertIn("project_url", form.errors)
        self.assertContains(response, 'value="Keep this title"')
        self.assertContains(response, escape(form.errors["project_url"][0]))
        self.assertEqual(Project.objects.count(), count)

    def test_title_filter_is_trimmed_case_insensitive_and_preserved_in_form(self):
        response = self.client.get(reverse("main:show_projects"), {"title": "  fOcUsBuDdY  "})

        self.assertEqual(response.context["title_query"], "fOcUsBuDdY")
        self.assertContains(response, 'value="fOcUsBuDdY"')
        payload = self.client.get(reverse("main:get_projects_json"), {"title": "  fOcUsBuDdY  "}).json()
        self.assertEqual([item["pk"] for item in payload], [str(self.project.pk)])

    def test_empty_and_no_match_api_results_leave_empty_state_available(self):
        response = self.client.get(reverse("main:show_projects"), {"title": "No matching project"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("main:get_projects_json"), {"title": "No matching project"}).json(), [])
        self.assertContains(response, 'id="empty"')

        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_projects"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("main:get_projects_json")).json(), [])
        self.assertEqual(response.context["title_query"], "")
        self.assertContains(response, 'id="empty"')

    def test_project_and_search_text_are_html_escaped(self):
        title = '<script>alert("title")</script>'
        description = '<img src=x onerror="alert(1)">'
        self.project.title = title
        self.project.description = description
        self.project.save()
        response = self.client.get(reverse("main:show_projects"))

        self.assertNotContains(response, title)
        self.assertNotContains(response, description)
        # Legacy database content remains data; browser coverage verifies safe
        # DOM rendering, and detail pages continue to use Django autoescaping.
        detail = self.client.get(reverse("main:project_detail", args=[self.project.pk]))
        self.assertContains(detail, escape(title))
        self.assertContains(detail, escape(description))
        self.assertNotContains(detail, title)
        self.assertNotContains(detail, description)

        response = self.client.get(reverse("main:show_projects"), {"title": title})
        self.assertContains(response, escape(title))
        self.assertNotContains(response, title)

    def test_list_defers_database_loading_to_the_browser(self):
        with patch("main.views.get_projects_json") as json_view, patch("main.views.public_projects") as query:
            response = self.client.get(reverse("main:show_projects"))

        json_view.assert_not_called()
        query.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("project_list", response.context)
        self.assertContains(response, reverse("main:get_projects_json"))
        self.assertNotContains(response, self.project.title)

    def test_delete_confirmation_posts_with_csrf_and_unique_project_target(self):
        self.client.force_login(self.admin)
        for project in (self.project, self.other_project):
            response = self.client.get(reverse("main:project_detail", args=[project.pk]))
            self.assertTemplateUsed(response, "components/project_delete_modal.html")
            # Detail retains one star form and one delete confirmation form.
            self.assertContains(response, 'name="csrfmiddlewaretoken"', count=2)
            self.assertContains(
                response,
                f'action="{reverse("main:delete_project", args=[project.pk])}"',
                count=1,
            )
            self.assertContains(response, f'id="delete-project-{project.pk}"', count=1)

    def test_get_delete_never_deletes(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("main:delete_project", args=[self.project.pk]))

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_post_delete_removes_only_target_and_shows_success(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("main:delete_project", args=[self.project.pk]), follow=True
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(Project.objects.filter(pk=self.other_project.pk).exists())
        self.assertContains(response, "Proyek berhasil dihapus!")

    def test_delete_unknown_or_malformed_uuid_returns_404(self):
        self.client.force_login(self.admin)
        missing_url = reverse("main:delete_project", args=[uuid.uuid4()])
        for method in (self.client.get, self.client.post):
            with self.subTest(method=method.__name__):
                self.assertEqual(method(missing_url).status_code, 404)
                self.assertEqual(method("/projects/not-a-uuid/delete/").status_code, 404)


class ProjectDataDeliveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Project.objects.all().delete()
        cls.project = Project.objects.create(**project_data(title="FocusBuddy & Noe"))
        cls.other_project = Project.objects.create(**project_data(title="Portfolio"))

    def test_json_preserves_serializer_fields_with_aggregate_star_metadata(self):
        response = self.client.get(reverse("main:get_projects_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        payload = response.json()
        self.assertEqual({item["pk"] for item in payload}, {str(self.project.pk), str(self.other_project.pk)})
        for item in payload:
            self.assertEqual(item["model"], "main.project")
            self.assertEqual(set(item["fields"]), set(project_data()) | {"star_count", "is_starred"})
            self.assertNotIn("starred_by", item["fields"])
            self.assertNotIn("starred_by_names", item["fields"])
            self.assertEqual(item["fields"]["star_count"], 0)
            self.assertIs(item["fields"]["is_starred"], False)
        model_payload = [
            {**item, "fields": {key: value for key, value in item["fields"].items() if key in project_data()}}
            for item in payload
        ]
        objects = [item.object for item in serializers.deserialize("json", json.dumps(model_payload))]
        self.assertEqual({obj.pk for obj in objects}, {self.project.pk, self.other_project.pk})
        self.assertTrue(all(isinstance(obj, Project) for obj in objects))

    def test_html_json_and_xml_have_matching_filtered_results(self):
        for query, expected in (
            ("  fOcUsBuDdY  ", {self.project.pk}),
            ("Portfolio", {self.other_project.pk}),
            ("   ", {self.project.pk, self.other_project.pk}),
            ("does not exist", set()),
        ):
            with self.subTest(query=query):
                params = {"title": query}
                html_response = self.client.get(reverse("main:show_projects"), params)
                json_response = self.client.get(reverse("main:get_projects_json"), params)
                xml_response = self.client.get(reverse("main:get_projects_xml"), params)

                self.assertEqual(html_response.status_code, 200)
                self.assertEqual(json_response.status_code, 200)
                self.assertEqual(xml_response.status_code, 200)
                self.assertEqual(xml_response["Content-Type"], "application/xml")
                self.assertEqual(html_response.context["title_query"], query.strip())
                self.assertNotIn("project_list", html_response.context)
                self.assertEqual({uuid.UUID(item["pk"]) for item in json_response.json()}, expected)
                root = ElementTree.fromstring(xml_response.content)
                self.assertEqual(root.tag, "django-objects")
                self.assertEqual({uuid.UUID(item.attrib["pk"]) for item in root.findall("object")}, expected)

    def test_empty_database_returns_empty_json_and_valid_xml(self):
        Project.objects.all().delete()
        json_response = self.client.get(reverse("main:get_projects_json"))
        xml_response = self.client.get(reverse("main:get_projects_xml"))

        self.assertEqual(json_response.json(), [])
        self.assertEqual(ElementTree.fromstring(xml_response.content).findall("object"), [])

    def test_xml_preserves_text_with_special_characters(self):
        response = self.client.get(reverse("main:get_projects_xml"))
        root = ElementTree.fromstring(response.content)
        titles = [field.text for field in root.findall("object/field[@name='title']")]

        self.assertIn("FocusBuddy & Noe", titles)


class ProjectCsrfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="csrf_admin")

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.csrf_client.force_login(self.admin)
        self.project = Project.objects.create(**project_data(title="Keep unless authorized"))

    def test_create_and_delete_without_csrf_token_are_rejected(self):
        count = Project.objects.count()
        create_response = self.csrf_client.post(reverse("main:create_project"), project_data())
        delete_response = self.csrf_client.post(
            reverse("main:delete_project", args=[self.project.pk])
        )

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        self.assertEqual(Project.objects.count(), count)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_create_and_delete_work_with_real_csrf_cookie_and_token(self):
        self.csrf_client.get(reverse("main:create_project"))
        token = self.csrf_client.cookies[settings.CSRF_COOKIE_NAME].value
        data = project_data(title="Created with CSRF", csrfmiddlewaretoken=token)
        create_response = self.csrf_client.post(reverse("main:create_project"), data)

        self.assertRedirects(create_response, reverse("main:show_projects"))
        project = Project.objects.get(title=data["title"])
        delete_response = self.csrf_client.post(
            reverse("main:delete_project", args=[project.pk]),
            {"csrfmiddlewaretoken": token},
        )
        self.assertRedirects(delete_response, reverse("main:show_projects"))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_pws_origin_is_trusted_without_trailing_slash(self):
        origin = "https://noe-andrew-myportofolio.pws.cs.ui.ac.id"
        self.assertIn(origin, settings.CSRF_TRUSTED_ORIGINS)
        self.assertNotIn(origin + "/", settings.CSRF_TRUSTED_ORIGINS)
        self.csrf_client.get(reverse("main:create_project"), secure=True, HTTP_HOST="localhost")
        token = self.csrf_client.cookies[settings.CSRF_COOKIE_NAME].value
        response = self.csrf_client.post(
            reverse("main:create_project"),
            project_data(title="Trusted PWS origin", csrfmiddlewaretoken=token),
            secure=True,
            HTTP_HOST="localhost",
            HTTP_ORIGIN=origin,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(title="Trusted PWS origin").exists())

    def test_untrusted_origin_is_rejected_even_with_valid_token(self):
        self.csrf_client.get(reverse("main:create_project"), secure=True, HTTP_HOST="localhost")
        token = self.csrf_client.cookies[settings.CSRF_COOKIE_NAME].value
        count = Project.objects.count()
        response = self.csrf_client.post(
            reverse("main:create_project"),
            project_data(csrfmiddlewaretoken=token),
            secure=True,
            HTTP_HOST="localhost",
            HTTP_ORIGIN="https://untrusted.example",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Project.objects.count(), count)
