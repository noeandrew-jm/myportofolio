import uuid
from unittest.mock import patch
from xml.etree import ElementTree

from django.conf import settings
from django.core import serializers
from django.http import HttpResponse
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

    def test_list_displays_database_fields_and_optional_links(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertEqual(
            {project.pk for project in response.context["project_list"]},
            {self.project.pk, self.other_project.pk},
        )
        for project in (self.project, self.other_project):
            self.assertContains(response, project.title)
            self.assertContains(response, project.description)
            self.assertContains(response, project.tech_stack)
        self.assertContains(response, f'href="{escape(self.project.project_url)}"')
        self.assertContains(response, f'src="{self.project.project_image_url}"')
        self.assertNotContains(response, 'src=""')
        self.assertContains(response, f'href="{reverse("main:create_project")}"')

    def test_get_form_is_unbound_and_does_not_create_data(self):
        count = Project.objects.count()
        response = self.client.get(reverse("main:create_project"))

        self.assertFalse(response.context["form"].is_bound)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertEqual(Project.objects.count(), count)

    def test_valid_post_saves_and_redirects_with_visible_success_message(self):
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
        self.assertContains(response, saved.title)

    def test_post_can_create_without_optional_urls(self):
        data = project_data(title="Text only project")
        data.pop("project_url")
        data.pop("project_image_url")
        response = self.client.post(reverse("main:create_project"), data)

        self.assertRedirects(response, reverse("main:show_projects"))
        saved = Project.objects.get(title=data["title"])
        self.assertEqual(saved.project_url, "")
        self.assertEqual(saved.project_image_url, "")

    def test_empty_post_returns_bound_errors_and_does_not_save(self):
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
        self.assertEqual([p.pk for p in response.context["project_list"]], [self.project.pk])
        self.assertContains(response, self.project.title)
        self.assertNotContains(response, self.other_project.title)
        self.assertContains(response, 'value="fOcUsBuDdY"')

    def test_empty_and_no_match_lists_render_empty_states(self):
        response = self.client.get(reverse("main:show_projects"), {"title": "No matching project"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["project_list"]), [])
        self.assertContains(response, 'class="empty-state"')
        self.assertContains(response, "Tidak ada proyek dengan nama tersebut.")

        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_projects"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["project_list"]), [])
        self.assertEqual(response.context["title_query"], "")
        self.assertContains(response, 'class="empty-state"')
        self.assertContains(response, "Belum ada proyek yang ditambahkan.")

    def test_project_and_search_text_are_html_escaped(self):
        title = '<script>alert("title")</script>'
        description = '<img src=x onerror="alert(1)">'
        self.project.title = title
        self.project.description = description
        self.project.save()
        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, escape(title))
        self.assertContains(response, escape(description))
        self.assertNotContains(response, title)
        self.assertNotContains(response, description)

        response = self.client.get(reverse("main:show_projects"), {"title": title})
        self.assertContains(response, escape(title))
        self.assertNotContains(response, title)

    def test_list_consumes_the_serialized_json_response(self):
        serialized_project = Project(**project_data(title="Serialized response project"))
        api_response = HttpResponse(
            serializers.serialize("json", [serialized_project]),
            content_type="application/json",
        )
        with patch("main.views.get_projects_json", return_value=api_response) as json_view:
            response = self.client.get(reverse("main:show_projects"))

        json_view.assert_called_once()
        self.assertEqual(response.status_code, 200)
        objects = list(response.context["project_list"])
        self.assertEqual(len(objects), 1)
        self.assertIsInstance(objects[0], Project)
        self.assertEqual(objects[0].pk, serialized_project.pk)
        self.assertContains(response, serialized_project.title)
        self.assertNotContains(response, self.project.title)

    def test_delete_confirmation_posts_with_csrf_and_unique_project_target(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertTemplateUsed(response, "components/project_delete_modal.html")
        self.assertContains(response, 'name="csrfmiddlewaretoken"', count=2)
        for project in (self.project, self.other_project):
            self.assertContains(
                response,
                f'action="{reverse("main:delete_project", args=[project.pk])}"',
                count=1,
            )
            self.assertContains(response, f'id="delete-project-{project.pk}"', count=1)

    def test_get_delete_never_deletes(self):
        response = self.client.get(reverse("main:delete_project", args=[self.project.pk]))

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_post_delete_removes_only_target_and_shows_success(self):
        response = self.client.post(
            reverse("main:delete_project", args=[self.project.pk]), follow=True
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(Project.objects.filter(pk=self.other_project.pk).exists())
        self.assertContains(response, "Proyek berhasil dihapus!")

    def test_delete_unknown_or_malformed_uuid_returns_404(self):
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

    def test_json_is_django_serialization_and_round_trips(self):
        response = self.client.get(reverse("main:get_projects_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        payload = response.json()
        self.assertEqual({item["pk"] for item in payload}, {str(self.project.pk), str(self.other_project.pk)})
        for item in payload:
            self.assertEqual(item["model"], "main.project")
            self.assertEqual(set(item["fields"]), set(project_data()))
        objects = [item.object for item in serializers.deserialize("json", response.content)]
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
                self.assertEqual({obj.pk for obj in html_response.context["project_list"]}, expected)
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
    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
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
