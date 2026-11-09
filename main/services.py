"""Content mutations shared by classic Django views and the versioned API."""

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404


@transaction.atomic(savepoint=False)
def toggle_content_star(model, content_id, user):
    """Toggle only ``user``'s membership and return the locked content object.

    Callers pass the authenticated request user, never an account from request
    data. PostgreSQL serializes toggles on the same content row until the outer
    transaction commits. SQLite ignores row locks; the M2M uniqueness constraint
    still prevents duplicate memberships, but does not serialize every toggle.

    API callers keep an outer transaction open while reading the response so its
    count and viewer status describe this mutation. ``savepoint=False`` avoids
    adding a redundant savepoint inside that existing transaction.
    """
    if not user.is_authenticated:
        raise PermissionDenied("Login is required to star portfolio entries.")

    content = get_object_or_404(model.objects.select_for_update(), pk=content_id)
    if content.starred_by.filter(pk=user.pk).exists():
        content.starred_by.remove(user)
    else:
        content.starred_by.add(user)
    return content
