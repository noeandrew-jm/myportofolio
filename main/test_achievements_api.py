"""Achievement API and classic actions preserve the same four portfolio roles."""

import uuid

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from main.models import Achievement
from main.serializers import AchievementSerializer


def achievement_data(**overrides):
    data = {
        "title": "Campus innovation award",
        "description": "Built an accessible application with my team.",
        "award": "First place",
        "thumbnail": "/static/image/PKM.jpeg",
        "display_order": 3,
    }
    data.update(overrides)
    return data


class AchievementFixtures:
    @classmethod
    def setUpTestData(cls):
        # Isolate seeded portfolio records inside the test database only.
        Achievement.objects.all().delete()
        cls.password = "achievement-test-only-password"
        cls.owner = User.objects.create_superuser(
            username="achievement-owner", password=cls.password,
            email="private-owner@example.com",
        )
        cls.member = User.objects.create_user(
            username="achievement-member", password=cls.password,
            email="private-member@example.com", first_name="Private",
            last_name="Account",
        )
        cls.editor = User.objects.create_user(
            username="achievement-editor", password=cls.password,
        )
        cls.editor.groups.add(Group.objects.get_or_create(name="Editor")[0])
        cls.achievement = Achievement.objects.create(**achievement_data())


class AchievementAPITests(AchievementFixtures, APITestCase):
    def setUp(self):
        self.list_url = reverse("api:achievement-list")
        self.detail_url = reverse("api:achievement-detail", args=[self.achievement.pk])
        self.star_url = reverse("api:achievement-star", args=[self.achievement.pk])

    def session_client(self, user):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username=user.username, password=self.password))
        return client

    def test_list_and_detail_are_public_for_every_role(self):
        for user in (None, self.member, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            with self.subTest(user=user):
                listing = self.client.get(self.list_url)
                detail = self.client.get(self.detail_url)
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(detail.status_code, 200)
                self.assertEqual(listing.data, [detail.data])
                self.assertEqual(detail.data["id"], str(self.achievement.pk))
                self.assertEqual(detail.data["star_count"], 0)
                self.assertIs(detail.data["is_starred"], False)
                self.assertEqual(set(detail.data), {
                    "id", "title", "description", "award", "thumbnail",
                    "display_order", "star_count", "is_starred",
                })

    def test_search_is_trimmed_case_insensitive_and_preserves_display_order(self):
        Achievement.objects.create(**achievement_data(title="Earlier award", display_order=1))
        response = self.client.get(self.list_url, {"title": "  CAMPUS  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data], [str(self.achievement.pk)])
        self.assertEqual(self.client.get(self.list_url, {"title": "missing"}).data, [])
        self.assertEqual(
            [row["title"] for row in self.client.get(self.list_url).data],
            ["Earlier award", self.achievement.title],
        )
        Achievement.objects.all().delete()
        self.assertEqual(self.client.get(self.list_url).data, [])

    def test_guest_and_member_cannot_create_update_or_delete(self):
        for user in (None, self.member):
            self.client.force_authenticate(user=user)
            for method, url, data in (
                ("post", self.list_url, achievement_data(title="Unauthorized new record")),
                ("put", self.detail_url, achievement_data(title="Unauthorized replacement")),
                ("patch", self.detail_url, {"title": "Unauthorized update"}),
                ("delete", self.detail_url, {}),
            ):
                with self.subTest(user=user, method=method):
                    response = getattr(self.client, method)(url, data, format="json")
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(Achievement.objects.count(), 1)
                    self.achievement.refresh_from_db()
                    self.assertEqual(self.achievement.title, "Campus innovation award")
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(self.star_url).status_code, 403)
        self.assertEqual(self.achievement.starred_by.count(), 0)

    def test_editor_can_put_patch_and_star_but_cannot_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"award": "Revised award"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.award, "Revised award")
        self.assertEqual(self.achievement.title, "Campus innovation award")
        response = self.client.put(self.detail_url, achievement_data(title="Editor replacement"), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Editor replacement")
        self.assertEqual(self.client.post(self.list_url, achievement_data(), format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Achievement.objects.count(), 1)
        self.assertIs(self.client.post(self.star_url).data["is_starred"], True)

    def test_owner_can_create_replace_patch_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, achievement_data(title="New award"), format="json")
        self.assertEqual(response.status_code, 201)
        created = Achievement.objects.get(pk=response.data["id"])
        self.assertEqual(created.title, "New award")
        self.assertEqual(Achievement.objects.count(), 2)
        response = self.client.put(self.detail_url, achievement_data(title="Replaced award"), format="json")
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(self.detail_url, {"description": "Revised description"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, "Replaced award")
        self.assertEqual(self.achievement.description, "Revised description")
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(Achievement.objects.filter(pk=self.achievement.pk).exists())
        self.assertTrue(Achievement.objects.filter(pk=created.pk).exists())

    def test_all_authenticated_roles_can_toggle_only_their_own_star(self):
        for user in (self.member, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            with self.subTest(user=user):
                response = self.client.post(self.star_url, {"user_id": self.owner.pk}, format="json")
                self.assertEqual(response.status_code, 200)
                self.assertIs(response.data["is_starred"], True)
                self.assertEqual(response.data["star_count"], 1)
                self.assertEqual(list(self.achievement.starred_by.all()), [user])
                response = self.client.post(self.star_url)
                self.assertEqual(response.status_code, 200)
                self.assertIs(response.data["is_starred"], False)
                self.assertEqual(response.data["star_count"], 0)
                self.assertEqual(self.achievement.starred_by.count(), 0)

    def test_star_status_is_viewer_specific_and_account_data_is_private(self):
        self.achievement.starred_by.add(self.member, self.editor)
        for user, expected in ((None, False), (self.owner, False), (self.member, True)):
            self.client.force_authenticate(user=user)
            for url in (self.list_url, self.detail_url):
                with self.subTest(user=user, url=url):
                    response = self.client.get(url)
                    record = response.data[0] if url == self.list_url else response.data
                    self.assertEqual(record["star_count"], 2)
                    self.assertIs(record["is_starred"], expected)
                    for field in ("starred_by", "starred_by_names", "email", "password", "username"):
                        self.assertNotIn(field, record)
                    for private_value in (self.member.email, self.member.password, self.member.username):
                        self.assertNotIn(private_value, response.content.decode())

    def test_id_and_computed_or_account_fields_cannot_be_written(self):
        self.client.force_authenticate(user=self.owner)
        forged_id = uuid.uuid4()
        forbidden_values = {
            "id": str(forged_id), "star_count": 999, "is_starred": True,
            "starred_by": [self.member.pk], "email": "forged@example.com",
        }
        response = self.client.post(self.list_url, {**achievement_data(), **forbidden_values}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data["id"], str(forged_id))
        self.assertEqual(response.data["star_count"], 0)
        self.assertIs(response.data["is_starred"], False)
        response = self.client.patch(self.detail_url, forbidden_values, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.achievement.pk))
        self.assertEqual(self.achievement.starred_by.count(), 0)

    def test_text_is_cleaned_on_create_put_and_patch(self):
        self.client.force_authenticate(user=self.owner)
        data = achievement_data(
            title="  <b>Campus award</b>  ", description=" <p>A <em>team</em> effort.</p> ",
            award=" <strong>Gold</strong> ",
        )
        for method, url in (("post", self.list_url), ("put", self.detail_url), ("patch", self.detail_url)):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, data, format="json")
                self.assertEqual(response.status_code, 201 if method == "post" else 200)
                saved = Achievement.objects.get(pk=response.data["id"])
                self.assertEqual(saved.title, "Campus award")
                self.assertEqual(saved.description, "A team effort.")
                self.assertEqual(saved.award, "Gold")

    def test_invalid_required_text_and_order_leave_saved_data_unchanged(self):
        self.client.force_authenticate(user=self.owner)
        invalid_values = [
            (field, value)
            for field in ("title", "description")
            for value in ("", "   ", "<p> </p>", '<img src="x" onerror="alert(1)">')
        ] + [("display_order", -1), ("display_order", "not-a-number"), ("title", "x" * 256)]
        for field, value in invalid_values:
            for method, url, data in (
                ("post", self.list_url, {**achievement_data(), field: value}),
                ("patch", self.detail_url, {field: value}),
            ):
                with self.subTest(field=field, value=value, method=method):
                    response = getattr(self.client, method)(url, data, format="json")
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(field, response.data)
        self.assertEqual(Achievement.objects.count(), 1)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, "Campus innovation award")
        self.assertEqual(self.achievement.display_order, 3)

    def test_optional_fields_and_safe_image_paths_remain_compatible_with_existing_data(self):
        self.client.force_authenticate(user=self.owner)
        for thumbnail in (
            "", "/static/image/PKM.jpeg", "/static/image/RISTEK%20HACKATHON.jpeg",
            "https://example.com/award.png?width=800&height=600", "http://example.com/award.png",
        ):
            with self.subTest(thumbnail=thumbnail):
                response = self.client.patch(
                    self.detail_url, {"award": "<b></b>", "thumbnail": thumbnail}, format="json",
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["award"], "")
                self.assertEqual(response.data["thumbnail"], thumbnail)

    def test_unsafe_thumbnails_are_rejected_on_create_and_update(self):
        self.client.force_authenticate(user=self.owner)
        for thumbnail in (
            "javascript:alert(1)", "data:text/html,<script>alert(1)</script>",
            "ftp://example.com/image.png", "//attacker.example/image.png", "not-a-url",
            "/static/../admin/", "/static/%2e%2e/admin/", "/static/\\attacker.example/image.png",
            "/static/%5c..%5cadmin/", "/static/%00image.png", "/static/a%0ab.png",
            "/static/", "https://[broken",
        ):
            for method, url, data in (
                ("post", self.list_url, achievement_data(thumbnail=thumbnail)),
                ("patch", self.detail_url, {"thumbnail": thumbnail}),
            ):
                with self.subTest(thumbnail=thumbnail, method=method):
                    response = getattr(self.client, method)(url, data, format="json")
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("thumbnail", response.data)
        self.assertEqual(Achievement.objects.count(), 1)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.thumbnail, "/static/image/PKM.jpeg")

    def test_put_requires_complete_required_fields_but_patch_does_not(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.put(self.detail_url, {"title": "Partial"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.data)
        response = self.client.patch(self.detail_url, {"title": "Partial"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.description, achievement_data()["description"])

    def test_missing_record_and_unsupported_methods(self):
        missing = uuid.uuid4()
        self.assertEqual(self.client.get(reverse("api:achievement-detail", args=[missing])).status_code, 404)
        self.client.force_authenticate(user=self.owner)
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(missing_method=method):
                response = getattr(self.client, method)(reverse("api:achievement-detail", args=[missing]), {}, format="json")
                self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.post(reverse("api:achievement-star", args=[missing])).status_code, 404)
        for method, url in (
            ("put", self.list_url), ("patch", self.list_url), ("delete", self.list_url),
            ("post", self.detail_url), ("get", self.star_url), ("put", self.star_url),
            ("patch", self.star_url), ("delete", self.star_url),
        ):
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(self.client, method)(url, {}, format="json").status_code, 405)
        self.assertEqual(Achievement.objects.count(), 1)
        self.assertEqual(self.achievement.starred_by.count(), 0)

    def test_safe_methods_never_modify_content_or_stars(self):
        self.achievement.starred_by.add(self.member)
        for user in (None, self.member, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            for method in ("get", "head", "options"):
                for url in (self.list_url, self.detail_url):
                    with self.subTest(user=user, method=method, url=url):
                        self.assertEqual(getattr(self.client, method)(url).status_code, 200)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, achievement_data()["title"])
        self.assertEqual(list(self.achievement.starred_by.all()), [self.member])
        self.assertEqual(Achievement.objects.count(), 1)

    def test_list_queries_do_not_grow_with_records_or_star_users(self):
        for index in range(6):
            item = Achievement.objects.create(**achievement_data(title=f"Award {index}"))
            item.starred_by.add(self.member, self.owner)
        for user in (None, self.member):
            self.client.force_authenticate(user=user)
            with self.subTest(user=user), CaptureQueriesContext(connection) as queries:
                response = self.client.get(self.list_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.data), 7)
            self.assertLessEqual(len(queries), 2)

    def test_real_session_writes_require_csrf_and_valid_origin(self):
        client = self.session_client(self.owner)
        actions = (
            ("post", self.list_url), ("put", self.detail_url),
            ("patch", self.detail_url), ("delete", self.detail_url), ("post", self.star_url),
        )
        for method, url in actions:
            with self.subTest(method=method, url=url):
                response = getattr(client, method)(url, achievement_data(), format="json")
                self.assertEqual(response.status_code, 403)
                self.assertIn("CSRF", str(response.data["detail"]))
        client.get(reverse("main:show_achievements"))
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        for headers in (
            {"HTTP_X_CSRFTOKEN": "invalid-token"},
            {"HTTP_X_CSRFTOKEN": token, "HTTP_ORIGIN": "https://attacker.example"},
        ):
            response = client.post(self.list_url, achievement_data(), format="json", **headers)
            self.assertEqual(response.status_code, 403)
        self.assertEqual(Achievement.objects.count(), 1)
        self.assertEqual(self.achievement.starred_by.count(), 0)

    def test_real_session_writes_with_csrf_succeed(self):
        client = self.session_client(self.owner)
        client.get(reverse("main:show_achievements"))
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        headers = {"format": "json", "HTTP_X_CSRFTOKEN": token}
        self.assertEqual(client.post(self.list_url, achievement_data(), **headers).status_code, 201)
        self.assertEqual(client.put(self.detail_url, achievement_data(), **headers).status_code, 200)
        self.assertEqual(client.patch(self.detail_url, {"award": "Gold"}, **headers).status_code, 200)
        self.assertEqual(client.post(self.star_url, {}, **headers).status_code, 200)
        self.assertEqual(client.delete(self.detail_url, **headers).status_code, 204)

    def test_member_page_supplies_csrf_for_star_without_owner_form(self):
        client = self.session_client(self.member)
        client.cookies.pop(settings.CSRF_COOKIE_NAME, None)
        page = client.get(reverse("main:show_achievements"))
        self.assertEqual(page.status_code, 200)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(self.star_url, {}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.data["is_starred"], True)

    def test_malformed_json_does_not_create_record(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, '{"title":', content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Achievement.objects.count(), 1)

    def test_serializer_works_without_request_or_annotated_queryset(self):
        self.achievement.starred_by.add(self.member)
        data = AchievementSerializer(self.achievement).data
        self.assertEqual(data["star_count"], 1)
        self.assertIs(data["is_starred"], False)

    def test_legacy_unsafe_images_are_omitted_without_rewriting_existing_data(self):
        for thumbnail in ("javascript:alert(1)", "//attacker.example/image.png", "https://[broken"):
            self.achievement.thumbnail = thumbnail
            self.achievement.save(update_fields=["thumbnail"])
            with self.subTest(thumbnail=thumbnail):
                response = self.client.get(self.detail_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["thumbnail"], "")
                self.achievement.refresh_from_db()
                self.assertEqual(self.achievement.thumbnail, thumbnail)


class AchievementClassicRoleTests(AchievementFixtures, TestCase):
    def setUp(self):
        self.list_url = reverse("main:show_achievements")
        self.detail_url = reverse("main:achievement_detail", args=[self.achievement.pk])
        self.create_url = reverse("main:create_achievement")
        self.edit_url = reverse("main:update_achievement", args=[self.achievement.pk])
        self.delete_url = reverse("main:delete_achievement", args=[self.achievement.pk])
        self.star_url = reverse("main:toggle_achievement_star", args=[self.achievement.pk])

    def test_public_pages_and_unauthenticated_actions(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertEqual(self.client.get(self.detail_url).status_code, 200)
        for url in (self.create_url, self.edit_url, self.delete_url, self.star_url):
            with self.subTest(url=url):
                response = self.client.post(url, achievement_data(title="Unauthorized"))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("main:login")))
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, achievement_data()["title"])
        self.assertEqual(Achievement.objects.count(), 1)
        self.assertEqual(self.achievement.starred_by.count(), 0)

    def test_member_cannot_mutate_content_and_editor_can_only_edit(self):
        for user, forbidden_urls in (
            (self.member, (self.create_url, self.edit_url, self.delete_url)),
            (self.editor, (self.create_url, self.delete_url)),
        ):
            self.client.force_login(user)
            for url in forbidden_urls:
                for method in ("get", "post"):
                    with self.subTest(user=user, method=method, url=url):
                        response = getattr(self.client, method)(url, achievement_data(title="Unauthorized"))
                        expected_status = 405 if method == "get" and url == self.delete_url else 403
                        self.assertEqual(response.status_code, expected_status)
            self.assertEqual(self.client.post(self.star_url).status_code, 302)
            self.assertTrue(self.achievement.starred_by.filter(pk=user.pk).exists())
            self.client.post(self.star_url)
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(self.edit_url).status_code, 200)
        response = self.client.post(self.edit_url, achievement_data(title="  <b>Edited achievement</b>  "))
        self.assertEqual(response.status_code, 302)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, "Edited achievement")
        self.assertEqual(Achievement.objects.count(), 1)

    def test_owner_classic_crud_uses_validated_form(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.create_url).status_code, 200)
        response = self.client.post(self.create_url, achievement_data(title=" <b>New classic award</b> "))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Achievement.objects.filter(title="New classic award").exists())
        response = self.client.post(self.edit_url, achievement_data(description=" <p>Revised description</p> "))
        self.assertEqual(response.status_code, 302)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.description, "Revised description")
        self.assertEqual(self.client.get(self.delete_url).status_code, 405)
        self.assertTrue(Achievement.objects.filter(pk=self.achievement.pk).exists())
        self.assertEqual(self.client.post(self.delete_url).status_code, 302)
        self.assertFalse(Achievement.objects.filter(pk=self.achievement.pk).exists())

    def test_invalid_classic_input_cannot_bypass_api_validation(self):
        self.client.force_login(self.owner)
        for field, value in (
            ("title", "<p></p>"), ("description", "<br>"),
            ("thumbnail", "javascript:alert(1)"), ("display_order", -1),
        ):
            for url in (self.create_url, self.edit_url):
                with self.subTest(field=field, url=url):
                    response = self.client.post(url, achievement_data(**{field: value}))
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(field, response.context["form"].errors)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, achievement_data()["title"])
        self.assertEqual(Achievement.objects.count(), 1)

    def test_classic_writes_require_csrf_and_star_get_is_read_only(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (self.create_url, self.edit_url, self.delete_url, self.star_url):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, achievement_data()).status_code, 403)
        self.assertEqual(client.get(self.star_url).status_code, 405)
        self.assertEqual(self.achievement.starred_by.count(), 0)
        client.get(self.edit_url)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(self.edit_url, achievement_data(title="Verified session", csrfmiddlewaretoken=token))
        self.assertEqual(response.status_code, 302)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, "Verified session")

    def test_star_redirect_cannot_leave_portfolio_host(self):
        self.client.force_login(self.member)
        response = self.client.post(self.star_url, {"next": "https://attacker.example/"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.url.startswith("https://attacker.example"))
        self.assertTrue(self.achievement.starred_by.filter(pk=self.member.pk).exists())

    def test_admin_permissions_cannot_bypass_the_portfolio_role_policy(self):
        permissions = Permission.objects.filter(
            content_type__app_label="main", content_type__model="achievement",
        )
        create_url = reverse("admin:main_achievement_add")
        edit_url = reverse("admin:main_achievement_change", args=[self.achievement.pk])
        delete_url = reverse("admin:main_achievement_delete", args=[self.achievement.pk])
        for user, forbidden_urls in (
            (self.member, (create_url, edit_url, delete_url)),
            (self.editor, (create_url, delete_url)),
        ):
            user.is_staff = True
            user.save(update_fields=["is_staff"])
            user.user_permissions.add(*permissions)
            self.client.force_login(user)
            for url in forbidden_urls:
                with self.subTest(user=user, url=url):
                    response = self.client.post(url, achievement_data(title="Unauthorized admin update"))
                    self.assertEqual(response.status_code, 403)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, achievement_data()["title"])
        self.assertEqual(Achievement.objects.count(), 1)
