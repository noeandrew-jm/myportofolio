import uuid

from django.db import migrations


# Preserve the owner's existing portfolio content when upgrading an empty database.
ACHIEVEMENTS = [
    {
        "id": uuid.UUID("ad86b93c-8272-4ec4-a705-2976ed3b9831"),
        "title": "RISTEK Hackathon 2026 Winner - FocusBuddy & Best Exhibition",
        "description": (
            "Won RISTEK Hackathon 2026 with FocusBuddy, an AI-powered productivity "
            "platform. As software engineer, built complete stack (frontend, "
            "backend, Google Auth) and designed AI/ML pipeline for task "
            "decomposition, duration prediction, and personalized recommendations. "
            "Delivered production-ready solution in six days."
        ),
        "award": "",
        "thumbnail": "/static/image/RISTEK%20HACKATHON.jpeg",
        "display_order": 0,
    },
    {
        "id": uuid.UUID("2fb3b7f8-5f55-48c4-b2f0-1f8a5b4efbe0"),
        "title": "PKM - GFT Universitas Indonesia",
        "description": (
            "Won third place for IoT-enabled algae cultivation system addressing "
            "indoor oxygen deficiency. Designed integrated solution combining "
            "natural oxygen generation through algae with smart sensor network "
            "for automated oxygen distribution across building zones. Focused on "
            "sustainable, cost-effective air quality management for "
            "under-resourced environments."
        ),
        "award": "Third Place Winner",
        "thumbnail": "/static/image/PKM.jpeg",
        "display_order": 1,
    },
]


def seed_achievements(apps, schema_editor):
    achievement_model = apps.get_model("main", "Achievement")
    database = schema_editor.connection.alias
    for achievement in ACHIEVEMENTS:
        defaults = {key: value for key, value in achievement.items() if key != "id"}
        achievement_model.objects.using(database).get_or_create(
            id=achievement["id"], defaults=defaults,
        )


def remove_seeded_achievements(apps, schema_editor):
    achievement_model = apps.get_model("main", "Achievement")
    achievement_model.objects.using(schema_editor.connection.alias).filter(
        id__in=[achievement["id"] for achievement in ACHIEVEMENTS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("main", "0003_achievement")]

    operations = [
        migrations.RunPython(seed_achievements, remove_seeded_achievements),
    ]
