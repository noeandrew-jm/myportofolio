"""Authentication, authorization, and CSRF checks using an isolated test database."""

from datetime import datetime
import secrets

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.urls import reverse

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
        cls.admin = User.objects.create_superuser(username="super_project_user")
        cls.project = Project.objects.create(**project_payload(title="Existing project"))

    def test_anonymous_create_requests_redirect_to_login_without_saving(self):
        count = Project.objects.count()
        url = reverse("main:create_project")
        for method in (self.client.get, self.client.post):
            with self.subTest(method=method.__name__):
                data = project_payload() if method == self.client.post else {}
                response = method(url, data)
                self.assertRedirects(response, f'{reverse("main:login")}?next={url}')
                self.assertEqual(Project.objects.count(), count)

    def test_regular_and_staff_users_cannot_create_or_delete_projects(self):
        count = Project.objects.count()
        for user in (self.user, self.staff):
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

    def test_project_management_buttons_are_only_shown_to_superuser(self):
        for user in (None, self.user, self.staff, self.admin):
            with self.subTest(user=user):
                if user is None:
                    self.client.logout()
                else:
                    self.client.force_login(user)
                response = self.client.get(reverse("main:show_projects"))
                self.assertEqual(response.status_code, 200)
                assertion = self.assertContains if user == self.admin else self.assertNotContains
                assertion(response, f'href="{reverse("main:create_project")}"')
                assertion(
                    response,
                    f'action="{reverse("main:delete_project", args=[self.project.pk])}"',
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
        self.assertEqual(project["fields"]["starred_by"], [self.user.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("main:show_projects"))
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
