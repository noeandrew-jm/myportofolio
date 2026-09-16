from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from main.models import Achievement, Experience


class MainTest(TestCase):
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
        self.assertContains(response, '<dl class="meta-list">')

    def test_all_public_pages_share_layout_and_navigation(self):
        for route in ("show_main", "show_experience", "show_achievements", "show_projects", "create_project"):
            with self.subTest(route=route):
                response = self.client.get(reverse(f"main:{route}"))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "base.html")
                self.assertContains(response, 'aria-current="page"', count=1)
                self.assertContains(response, 'class="site-header"', count=1)
                self.assertContains(response, 'class="site-footer"', count=1)
                for destination in ("show_main", "show_experience", "show_achievements", "show_projects"):
                    self.assertContains(response, f'href="{reverse(f"main:{destination}")}"')


    def test_liquid_glass_assets_and_button_labels(self):
        self.assertIsNotNone(finders.find("js/liquid-glass.js"))
        for route, button_count in (("show_main", 7), ("show_experience", 4), ("show_achievements", 4), ("show_projects", 4), ("create_project", 4)):
            with self.subTest(route=route):
                response = self.client.get(reverse(f"main:{route}"))
                self.assertContains(response, 'src="/static/js/liquid-glass.js" defer', count=1)
                self.assertContains(response, 'class="glass-button__label"', count=button_count)
                # Effects must not replace the links or hide their accessible labels.
                self.assertNotContains(response, 'class="glass-button__label" aria-hidden')


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
        self.assertContains(response, achievement.description)
        self.assertContains(response, 'class="content-item content-item--text-only"')
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
