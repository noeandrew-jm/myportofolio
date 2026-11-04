"""Project roles shared by the server checks and template controls."""

from rest_framework.permissions import BasePermission, SAFE_METHODS

EDITOR_GROUP = "Editor"


def can_create_projects(user):
    return user.is_authenticated and user.is_superuser


def can_edit_projects(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=EDITOR_GROUP).exists()
    )


class IsPortfolioOwnerOrReadOnly(BasePermission):
    """Owner-only write policy from the tutorial's introductory example."""

    message = "Only the portfolio owner can change projects."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or can_create_projects(request.user)


class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    """Preserve the existing Projects assignment's Editor update permission."""

    message = "Only the owner can create/delete projects; Editors may update them."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.method in ("PUT", "PATCH"):
            return can_edit_projects(request.user)
        return can_create_projects(request.user)
