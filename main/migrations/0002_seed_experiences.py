from django.db import migrations


EXPERIENCES = [
    {
        "title": "IT DEV - DDP 0",
        "description": (
            "Built frontend and authentication system for DDP-0, a bootcamp "
            "platform serving 1,000+ students learning fundamental programming "
            "at Universitas Indonesia. Implemented responsive UI for registration "
            "and course management, integrated Google OAuth for secure access, "
            "and optimized application for high-volume concurrent users."
        ),
        "category": "part-time",
        "thumbnail": "/static/image/ddp0.jpg",
    },
    {
        "title": "Hackathon 2026 Winner - FocusBuddy",
        "description": (
            "As software engineer, built complete stack (frontend, backend, "
            "Google Auth) and designed AI/ML pipeline for task decomposition, "
            "duration prediction, and personalized recommendations. Delivered "
            "production-ready solution in six days."
        ),
        "category": "freelance",
        "thumbnail": "/static/image/focusbud.jpg",
    },
]


def seed_experiences(apps, schema_editor):
    experience_model = apps.get_model("main", "Experience")
    for experience in EXPERIENCES:
        experience_model.objects.get_or_create(
            title=experience["title"],
            defaults=experience,
        )


def remove_seeded_experiences(apps, schema_editor):
    experience_model = apps.get_model("main", "Experience")
    experience_model.objects.filter(
        title__in=[experience["title"] for experience in EXPERIENCES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_experiences, remove_seeded_experiences),
    ]