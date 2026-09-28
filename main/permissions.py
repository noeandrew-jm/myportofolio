"""Project roles shared by the server checks and template controls."""

EDITOR_GROUP = "Editor"


def can_edit_projects(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=EDITOR_GROUP).exists()
    )
