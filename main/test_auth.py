"""Authentication, authorization, and CSRF checks using an isolated test database."""

from datetime import datetime
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.html import escape

from main.models import Project


def project_payload(**overrides):
    data = {
        "title": "Authentication test project",
        "description": "Created only in the Django test database.",
        "tech_stack": "Django, Python",
    }
    data.update(overrides)
    return data


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = secrets.token_urlsafe(32)
        cls.user = get_user_model().objects.create_user(
            username="auth_test_user", password=cls.password
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def login(self, password=None):
        form_response = self.client.get(reverse("main:login"))
        return self.client.post(
            reverse("main:login"),
            {
                "username": self.user.username,
                "password": self.password if password is None else password,
                "csrfmiddlewaretoken": str(form_response.context["csrf_token"]),
            },
        )

    def test_login_form_provides_csrf_cookie_and_hidden_token(self):
        response = self.client.get(reverse("main:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertTrue(str(response.context["csrf_token"]))
        self.assertTrue(self.client.cookies[settings.CSRF_COOKIE_NAME].value)
        self.assertNotIn(settings.SESSION_COOKIE_NAME, self.client.cookies)

    def test_valid_login_creates_session_and_last_login_cookie(self):
        response = self.login()

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertTrue(self.client.cookies[settings.SESSION_COOKIE_NAME].value)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        last_login = self.client.cookies["last_login"].value
        self.assertIsInstance(datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S"), datetime)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)
        home = self.client.get(reverse("main:show_main"))
        self.assertContains(home, f'<span class="nav-user">{self.user.username}</span>')
        self.assertContains(home, "Sesi Terakhir Login")
        self.assertContains(home, last_login)
        self.assertEqual(home.context["last_login"], last_login)

    def test_invalid_password_does_not_create_authenticated_session(self):
        response = self.login(password=secrets.token_urlsafe(32))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertNotIn("last_login", self.client.cookies)

    def test_login_without_csrf_token_is_rejected(self):
        self.client.get(reverse("main:login"))
        response = self.client.post(
            reverse("main:login"),
            {"username": self.user.username, "password": self.password},
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertNotIn("last_login", self.client.cookies)

    def test_login_returns_to_safe_next_from_get_or_post(self):
        for next_url in ("/projects/?title=Portfolio", "http://testserver/projects/"):
            for source in ("get", "post"):
                with self.subTest(next_url=next_url, source=source):
                    self.client.logout()
                    login_url = reverse("main:login")
                    if source == "get":
                        login_url += "?" + urlencode({"next": next_url})
                    form = self.client.get(login_url)
                    data = {
                        "username": self.user.username,
                        "password": self.password,
                        "csrfmiddlewaretoken": str(form.context["csrf_token"]),
                    }
                    if source == "post":
                        data["next"] = next_url

                    response = self.client.post(login_url, data)

                    self.assertRedirects(response, next_url, fetch_redirect_response=False)
                    self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))

    def test_invalid_login_preserves_safe_return_destination(self):
        next_url = "/projects/?title=Portfolio&view=all"
        response = self.client.get(reverse("main:login"), {"next": next_url})
        self.assertContains(response, 'name="next"')
        self.assertContains(response, f'value="{escape(next_url)}"')

        response = self.client.post(
            reverse("main:login"),
            {
                "username": self.user.username,
                "password": "incorrect-password",
                "next": next_url,
                "csrfmiddlewaretoken": str(response.context["csrf_token"]),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertContains(response, f'value="{escape(next_url)}"')
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_login_rejects_external_and_unsafe_return_destinations(self):
        for next_url in (
            "https://untrusted.example/projects/",
            "//untrusted.example/projects/",
            "///untrusted.example/projects/",
            "http://testserver@untrusted.example/",
            "javascript:alert(1)",
        ):
            with self.subTest(next_url=next_url):
                self.client.logout()
                form = self.client.get(reverse("main:login"), {"next": next_url})
                response = self.client.post(
                    reverse("main:login"),
                    {
                        "username": self.user.username,
                        "password": self.password,
                        "next": next_url,
                        "csrfmiddlewaretoken": str(form.context["csrf_token"]),
                    },
                )
                self.assertRedirects(response, reverse("main:show_main"))

    def test_https_login_does_not_redirect_to_insecure_absolute_url(self):
        form = self.client.get(reverse("main:login"), secure=True)
        response = self.client.post(
            reverse("main:login"),
            {
                "username": self.user.username,
                "password": self.password,
                "next": "http://testserver/projects/",
                "csrfmiddlewaretoken": str(form.context["csrf_token"]),
            },
            secure=True,
            HTTP_REFERER="https://testserver/login/",
        )
        self.assertRedirects(response, reverse("main:show_main"))

    def test_logout_expires_cookies_and_invalidates_server_session(self):
        self.login()
        previous_session = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertTrue(Session.objects.filter(session_key=previous_session).exists())

        response = self.client.get(reverse("main:logout"))

        self.assertRedirects(response, reverse("main:show_main"))
        for name in (settings.SESSION_COOKIE_NAME, "last_login"):
            with self.subTest(cookie=name):
                self.assertEqual(response.cookies[name].value, "")
                self.assertEqual(response.cookies[name]["max-age"], 0)
        self.assertFalse(Session.objects.filter(session_key=previous_session).exists())
        home = self.client.get(reverse("main:show_main"))
        self.assertNotContains(home, 'class="nav-user"')
        self.assertContains(home, f'href="{reverse("main:login")}"')

        # A copy of the old session cookie must not restore authentication.
        stale_client = Client()
        stale_client.cookies[settings.SESSION_COOKIE_NAME] = previous_session
        response = stale_client.get(reverse("main:create_project"))
        self.assertRedirects(
            response,
            f'{reverse("main:login")}?next={reverse("main:create_project")}',
        )


class ProjectAuthorizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="regular_project_user")
        cls.staff = User.objects.create_user(username="staff_project_user", is_staff=True)
        cls.editor = User.objects.create_user(username="editor_project_user")
        cls.editor.groups.add(Group.objects.get(name="Editor"))
        cls.admin = User.objects.create_superuser(username="super_project_user")
        cls.project = Project.objects.create(**project_payload(title="Existing project"))

    def test_anonymous_management_requests_redirect_to_login_without_saving(self):
        count = Project.objects.count()
        for url in (
            reverse("main:create_project"),
            reverse("main:update_project", args=[self.project.pk]),
            reverse("main:delete_project", args=[self.project.pk]),
        ):
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    data = project_payload() if method == self.client.post else {}
                    response = method(url, data)
                    self.assertRedirects(response, f'{reverse("main:login")}?next={url}')
                    self.assertEqual(Project.objects.count(), count)
                    self.project.refresh_from_db()
                    self.assertEqual(self.project.title, "Existing project")

    def test_regular_staff_and_editor_users_cannot_create_or_delete_projects(self):
        count = Project.objects.count()
        for user in (self.user, self.staff, self.editor):
            self.client.force_login(user)
            for url in (
                reverse("main:create_project"),
                reverse("main:delete_project", args=[self.project.pk]),
            ):
                for method in (self.client.get, self.client.post):
                    with self.subTest(user=user.username, url=url, method=method.__name__):
                        response = method(url, project_payload())
                        self.assertEqual(response.status_code, 403)
                        self.assertEqual(Project.objects.count(), count)
                        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_regular_and_staff_users_cannot_update_projects(self):
        url = reverse("main:update_project", args=[self.project.pk])
        original = project_payload(title="Existing project")
        count = Project.objects.count()
        for user in (self.user, self.staff):
            self.client.force_login(user)
            for method in (self.client.get, self.client.post):
                with self.subTest(user=user.username, method=method.__name__):
                    response = method(url, project_payload(title="Unauthorized update"))
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(Project.objects.count(), count)
                    self.project.refresh_from_db()
                    for field, value in original.items():
                        self.assertEqual(getattr(self.project, field), value)

    def test_editor_and_superuser_can_update_without_creating_records(self):
        count = Project.objects.count()
        url = reverse("main:update_project", args=[self.project.pk])
        for user in (self.editor, self.admin):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["form"].instance.pk, self.project.pk)
                data = project_payload(title=f"Edited by {user.username}")
                response = self.client.post(url, data)
                self.assertRedirects(response, reverse("main:show_projects"))
                self.project.refresh_from_db()
                self.assertEqual(Project.objects.count(), count)
                for field, value in data.items():
                    self.assertEqual(getattr(self.project, field), value)

    def test_removing_editor_group_revokes_update_access_on_next_request(self):
        self.client.force_login(self.editor)
        url = reverse("main:update_project", args=[self.project.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.editor.groups.clear()

        response = self.client.post(url, project_payload(title="No longer allowed"))

        self.assertEqual(response.status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Existing project")

    def test_project_controls_follow_role_on_list_and_detail(self):
        for user in (None, self.user, self.staff, self.editor, self.admin):
            with self.subTest(user=user):
                if user is None:
                    self.client.logout()
                else:
                    self.client.force_login(user)
                owner_assertion = self.assertContains if user == self.admin else self.assertNotContains
                listing = self.client.get(reverse("main:show_projects"))
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(listing.context["can_edit_projects"], user in (self.editor, self.admin))
                owner_assertion(listing, 'id="add-project-modal"')
                owner_assertion(listing, 'id="project-form"')

                response = self.client.get(reverse("main:project_detail", args=[self.project.pk]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, self.project.title)
                owner_assertion(
                    response,
                    f'action="{reverse("main:delete_project", args=[self.project.pk])}"',
                )
                editor_assertion = self.assertContains if user in (self.editor, self.admin) else self.assertNotContains
                editor_assertion(
                    response,
                    f'href="{reverse("main:update_project", args=[self.project.pk])}"',
                )

    def test_superuser_can_open_form_and_create_project(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("main:create_project"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="project-form"')

        response = self.client.post(reverse("main:create_project"), project_payload())

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(Project.objects.filter(title="Authentication test project").exists())

    def test_regular_user_can_star_and_unstar_project_without_admin_access(self):
        self.client.force_login(self.user)
        url = reverse("main:toggle_star", args=[self.project.pk])

        response = self.client.post(url)

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertQuerySetEqual(self.project.starred_by.all(), [self.user])
        payload = self.client.get(reverse("main:get_projects_json")).json()
        project = next(item for item in payload if item["pk"] == str(self.project.pk))
        self.assertNotIn("starred_by", project["fields"])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(self.project.starred_by.exists())


class ProjectStarCsrfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="csrf_star_user")
        cls.project = Project.objects.create(**project_payload(title="Starred project"))

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        self.detail_url = reverse("main:project_detail", args=[self.project.pk])
        self.star_url = reverse("main:toggle_star", args=[self.project.pk])

    def test_star_requires_login_post_and_csrf_and_updates_display(self):
        anonymous_response = Client().post(self.star_url)
        self.assertRedirects(
            anonymous_response,
            f'{reverse("main:login")}?next={self.star_url}',
        )

        detail = self.client.get(self.detail_url)
        self.assertContains(detail, 'aria-pressed="false"')
        self.assertContains(detail, 'aria-label="0 star">0</span>')
        token = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(self.client.get(self.star_url).status_code, 405)

        missing_token = self.client.post(
            self.star_url,
            {"next": self.detail_url},
        )
        self.assertEqual(missing_token.status_code, 403)
        self.assertFalse(self.project.starred_by.exists())

        response = self.client.post(
            self.star_url,
            {"csrfmiddlewaretoken": token, "next": self.detail_url},
        )
        self.assertRedirects(response, self.detail_url)
        detail = self.client.get(self.detail_url)
        self.assertContains(detail, 'aria-pressed="true"')
        self.assertContains(detail, 'aria-label="1 star">1</span>')
        self.assertQuerySetEqual(self.project.starred_by.all(), [self.user])

        response = self.client.post(
            self.star_url,
            {"csrfmiddlewaretoken": token, "next": self.detail_url},
        )
        self.assertRedirects(response, self.detail_url)
        detail = self.client.get(self.detail_url)
        self.assertContains(detail, 'aria-pressed="false"')
        self.assertContains(detail, 'aria-label="0 star">0</span>')
        self.assertFalse(self.project.starred_by.exists())

class AuthenticatedProjectCsrfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="csrf_mutation_admin")

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.admin)
        self.url = reverse("main:create_project")
        self.form_response = self.client.get(self.url)

    def test_missing_empty_malformed_and_mismatched_tokens_never_save(self):
        cookie = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        different_token = ("a" if cookie[0] != "a" else "b") + cookie[1:]
        count = Project.objects.count()
        for token in (None, "", "invalid", different_token):
            with self.subTest(token_kind="missing" if token is None else len(token)):
                data = project_payload()
                if token is not None:
                    data["csrfmiddlewaretoken"] = token
                response = self.client.post(self.url, data)

                self.assertContains(response, "CSRF verification failed", status_code=403)
                self.assertEqual(Project.objects.count(), count)
                self.assertEqual(self.client.session[SESSION_KEY], str(self.admin.pk))

    def test_valid_form_token_with_authenticated_session_saves_project(self):
        count = Project.objects.count()
        data = project_payload(csrfmiddlewaretoken=str(self.form_response.context["csrf_token"]))

        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertEqual(Project.objects.count(), count + 1)
        self.assertTrue(Project.objects.filter(title=data["title"]).exists())
