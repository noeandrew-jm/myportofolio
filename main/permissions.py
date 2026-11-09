"""Portfolio roles shared by API checks, classic views, and template controls."""

from rest_framework.permissions import BasePermission, SAFE_METHODS

EDITOR_GROUP = "Editor"


def is_portfolio_owner(user):
    """Staff status alone never grants ownership of this personal portfolio."""
    return user.is_authenticated and user.is_superuser


def can_edit_portfolio(user):
    """Read current group membership; revoking Editor applies on the next request."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=EDITOR_GROUP).exists()
    )


def can_create_projects(user):
    return is_portfolio_owner(user)


def can_edit_projects(user):
    return can_edit_portfolio(user)


def can_create_achievements(user):
    return is_portfolio_owner(user)


def can_edit_achievements(user):
    return can_edit_portfolio(user)


class IsPortfolioOwnerOrReadOnly(BasePermission):
    """Owner-only write policy from the tutorial's introductory example."""

    message = "Only the portfolio owner can change projects."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_portfolio_owner(request.user)


class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    """Public reads, owner CRUD, and Editor updates for portfolio entries."""

    message = "Only the owner can create/delete entries; Editors may update them."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.method in ("PUT", "PATCH"):
            return can_edit_portfolio(request.user)
        return is_portfolio_owner(request.user)
