from django.db import migrations


LANJUT_EXPERIENCE = {
    "title": "Frontend, UI/UX, and Designer for Lanjut.id",
    "description": (
        "Designed and built the frontend, UI/UX, and pitch deck for LANJUT.ID, "
        "an AI Agent that converts merchant transaction data into relevant renewal offers. "
        "Crafted the merchant and BNI dashboard experience, "
        "translated the four-stage AI pipeline (Sense, Decide, Act, Learn) into an intuitive interface, "
        "and delivered the pitch narrative that positioned LANJUT.ID within the BNI ecosystem."
    ),
    "category": "freelance",
    "thumbnail": "/static/image/Lanjut.id.png",
}


def seed_lanjut_experience(apps, schema_editor):
    experience_model = apps.get_model("main", "Experience")
    experiences = experience_model.objects.using(schema_editor.connection.alias)
    # Keep any existing entry and its edits, including on databases seeded before this migration.
    if not experiences.filter(title=LANJUT_EXPERIENCE["title"]).exists():
        experiences.create(**LANJUT_EXPERIENCE)


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0005_project"),
    ]

    operations = [
        # Rolling back must not delete an experience the owner may have edited.
        migrations.RunPython(seed_lanjut_experience, migrations.RunPython.noop),
    ]
