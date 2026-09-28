from django.db import migrations


def create_editor_group(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.using(schema_editor.connection.alias).get_or_create(name="Editor")


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("main", "0007_project_starred_by"),
    ]

    operations = [
        # Preserve an existing group's memberships when applying or reversing.
        migrations.RunPython(create_editor_group, migrations.RunPython.noop),
    ]
