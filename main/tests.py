from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from main.models import Achievement, Experience


class NavigationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.navigations = []
        self.current_navigation = None
        self.navigation_glass_elements = []
        self.glass_elements = []
        self.asset_paths = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav":
            self.current_navigation = []
            self.navigations.append(self.current_navigation)
        if tag == "a" and self.current_navigation is not None:
            self.current_navigation.append(attrs)
        if "glass-button" in attrs.get("class", "").split():
            self.glass_elements.append((tag, attrs))
            if self.current_navigation is not None:
                self.navigation_glass_elements.append((tag, attrs))
        if tag in ("script", "link"):
            self.asset_paths.append(urlsplit(attrs.get("src", attrs.get("href", ""))).path)

    def handle_endtag(self, tag):
        if tag == "nav":
            self.current_navigation = None


class MainTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="navigation_admin")

    def setUp(self):
        # Data migrations also run in the test database. Isolate each test from
        # the portfolio's seeded entries without touching the real database.
        Experience.objects.all().delete()
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_landing_intro_links_to_existing_about_page(self):
        self.assertEqual(reverse("main:show_landing"), "/")
        self.assertEqual(reverse("main:show_main"), "/about/")
        response = self.client.get(reverse("main:show_landing"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")
        self.assertContains(response, "HI, I'm Noe Andrew!")
        self.assertContains(response, "Check this out")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')
        self.assertNotContains(response, '<nav')
        self.assertNotContains(response, self.experience.title)

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Ongoing since")
        self.assertNotContains(response, "Completed:")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "No experience has been added yet.")
        self.assertNotContains(response, self.experience.title)

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Completed:")
        self.assertNotContains(response, "Ongoing since")

    def test_profile_context_and_contact_links(self):
        response = self.client.get(reverse("main:show_main"))

        for key in ("name", "npm", "study_program", "bio"):
            self.assertContains(response, escape(response.context[key]))
        self.assertContains(response, 'href="mailto:noeandrewjms@gmail.com"')
        self.assertContains(response, 'href="https://www.linkedin.com/in/noeandrew"')
        document = NavigationParser()
        document.feed(response.content.decode())
        contact_links = [
            (tag, attrs)
            for tag, attrs in document.glass_elements
            if "profile-contact-link" in attrs.get("class", "").split()
        ]
        self.assertEqual(
            [attrs["href"] for _, attrs in contact_links],
            [
                "mailto:noeandrewjms@gmail.com",
                "https://github.com/noeandrew-jm",
                "https://www.linkedin.com/in/noeandrew",
            ],
        )
        for tag, attrs in contact_links:
            self.assertEqual(tag, "a")
            self.assertNotIn("aria-current", attrs)

    def test_all_public_pages_share_layout_and_navigation(self):
        for route in ("show_main", "show_experience", "show_achievements", "show_projects"):
            with self.subTest(route=route):
                response = self.client.get(reverse(f"main:{route}"))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "base.html")
                self.assertContains(response, 'aria-current="page"', count=1)
                self.assertContains(response, 'class="site-header"', count=1)
                self.assertContains(response, 'class="site-footer"', count=1)
                for destination in ("show_main", "show_experience", "show_achievements", "show_projects"):
                    self.assertContains(response, f'href="{reverse(f"main:{destination}")}"')


    def test_only_current_navigation_link_has_liquid_glass(self):
        self.assertIsNotNone(finders.find("js/liquid-glass.js"))
        destinations = ("show_main", "show_achievements", "show_experience", "show_projects")
        for route, active_route in (
            ("show_main", "show_main"),
            ("show_experience", "show_experience"),
            ("show_achievements", "show_achievements"),
            ("show_projects", "show_projects"),
            ("login", "login"),
            ("register", "register"),
            ("create_project", "show_projects"),
        ):
            with self.subTest(route=route):
                if route == "create_project":
                    self.client.force_login(self.admin)
                auth_destinations = ("logout",) if route == "create_project" else ("login", "register")
                expected_destinations = destinations + auth_destinations
                response = self.client.get(reverse(f"main:{route}"))
                document = NavigationParser()
                document.feed(response.content.decode())
                self.assertEqual(len(document.navigations), 1)
                links = document.navigations[0]
                self.assertEqual(len(links), len(expected_destinations))
                self.assertEqual(
                    [urlsplit(link["href"]).path for link in links],
                    [reverse(f"main:{destination}") for destination in expected_destinations],
                )
                for link in links:
                    classes = link.get("class", "").split()
                    link_path = urlsplit(link["href"]).path
                    is_active = link_path == reverse(f"main:{active_route}")
                    self.assertIn("nav-link", classes)
                    if is_active:
                        self.assertIn("active", classes)
                        self.assertIn("glass-button", classes)
                        self.assertEqual(link.get("aria-current"), "page")
                    else:
                        self.assertNotIn("active", classes)
                        self.assertNotIn("aria-current", link)
                        self.assertNotIn("glass-button", classes)
                expected_glass_links = [
                    ("a", link)
                    for link in links
                    if urlsplit(link["href"]).path == reverse(f"main:{active_route}")
                ]
                self.assertEqual(document.navigation_glass_elements, expected_glass_links)
                glass_toggles = [
                    (tag, attrs)
                    for tag, attrs in document.glass_elements
                    if "nav-toggle" in attrs.get("class", "").split()
                ]
                self.assertEqual(len(glass_toggles), 1)
                toggle_tag, toggle_attrs = glass_toggles[0]
                self.assertEqual(toggle_tag, "button")
                self.assertEqual(toggle_attrs.get("aria-controls"), "main-navigation")
                self.assertEqual(toggle_attrs.get("aria-expanded"), "false")
                self.assertTrue(toggle_attrs.get("aria-label"))
                self.assertEqual(document.asset_paths.count("/static/js/liquid-glass.js"), 1)
                self.assertEqual(
                    len(document.glass_elements),
                    len(expected_glass_links) + len(glass_toggles) + (3 if route == "show_main" else 0),
                )
                label_count = len(expected_destinations) + (3 if route == "show_main" else 0)
                self.assertContains(response, 'class="glass-button__label"', count=label_count)
                # Effects must not replace the links or hide their accessible labels.
                self.assertNotContains(response, 'class="glass-button__label" aria-hidden')

    def test_about_page_assets_are_available(self):
        response = self.client.get(reverse("main:show_main"))
        document = NavigationParser()
        document.feed(response.content.decode())
        for asset in ("js/about.js", "css/about.css"):
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset))
                self.assertIn(f"/static/{asset}", document.asset_paths)
        for image in ("moon.png", "object.png", "lego.png", "group.png"):
            with self.subTest(image=image):
                self.assertIsNotNone(finders.find(f"image/about/{image}"))


class AchievementTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Achievement.objects.all().delete()
        cls.achievement = Achievement.objects.create(
            title="Portfolio testing award",
            description="A unique description supplied by the database.",
            award="First Place",
            thumbnail="/static/image/PKM.jpeg",
            display_order=2,
        )

    def test_achievements_url_and_template(self):
        response = self.client.get(reverse("main:show_achievements"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "achievements.html")
        self.assertQuerySetEqual(response.context["achievement_list"], [self.achievement])

    def test_all_model_data_appears_on_page(self):
        another = Achievement.objects.create(
            title="Another database achievement",
            description="A second record must render without adding another HTML card.",
            display_order=1,
        )
        response = self.client.get(reverse("main:show_achievements"))

        for achievement in (self.achievement, another):
            self.assertContains(response, achievement.title)
            self.assertContains(response, achievement.description)
        self.assertContains(response, self.achievement.award)
        self.assertContains(response, f'src="{self.achievement.thumbnail}"')
        self.assertContains(response, '<article ', count=2)
        self.assertQuerySetEqual(response.context["achievement_list"], [another, self.achievement])
        self.assertNotContains(response, "No achievements have been added yet.")

    def test_empty_achievements_page(self):
        Achievement.objects.all().delete()
        response = self.client.get(reverse("main:show_achievements"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No achievements have been added yet.")
        self.assertNotContains(response, '<article ')
        self.assertNotContains(response, "RISTEK Hackathon 2026 Winner")
        self.assertNotContains(response, "PKM - GFT Universitas Indonesia")

    def test_model_and_optional_fields(self):
        achievement = Achievement(title="Without an image", description="Text-only achievement.")
        achievement.full_clean()
        achievement.save()
        response = self.client.get(reverse("main:show_achievements"))

        self.assertEqual(str(achievement), "Without an image")
        self.assertContains(response, achievement.title)
        self.assertContains(response, achievement.description)
        self.assertNotContains(response, 'src=""')

    def test_changed_model_data_is_reflected_on_page(self):
        previous_title = self.achievement.title
        self.achievement.title = "Updated achievement title"
        self.achievement.save()
        response = self.client.get(reverse("main:show_achievements"))

        self.assertContains(response, self.achievement.title)
        self.assertNotContains(response, previous_title)

    def test_model_text_is_escaped(self):
        self.achievement.description = '<script>alert("test")</script>'
        self.achievement.save()
        response = self.client.get(reverse("main:show_achievements"))

        self.assertContains(response, escape(self.achievement.description))
        self.assertNotContains(response, self.achievement.description)
