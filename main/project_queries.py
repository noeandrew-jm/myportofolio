"""Public project data and aggregate stars, without exposing account records."""

from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Count, Exists, OuterRef, Prefetch, Value

from main.models import Project


# Keep the tutorial's Django serializer shape, but never serialize user relations.
PUBLIC_PROJECT_FIELDS = (
    "title", "description", "tech_stack", "project_url", "project_image_url",
)


def public_projects(title_query=""):
    """Keep search behavior identical for the legacy endpoints and DRF API."""
    projects = Project.objects.all()
    title_query = title_query.strip()
    if title_query:
        projects = projects.filter(title__icontains=title_query)
    return projects


def projects_with_stars(title_query=""):
    """Load the API's public usernames with two queries, independent of list size.

    Project's existing API contract includes ``starred_by_names``. Prefetch only
    the user ID and username needed by the serializer, keeping email/password
    fields out of memory and avoiding a query for each project's star relation.
    """
    return public_projects(title_query).prefetch_related(Prefetch(
        "starred_by", queryset=get_user_model().objects.only("id", "username"),
    )).order_by("title", "id")


def with_star_status(projects, user):
    """Calculate count and viewer status in one query, regardless of card count."""
    is_starred = Value(False, output_field=BooleanField())
    if user.is_authenticated:
        is_starred = Exists(
            Project.starred_by.through.objects.filter(
                project_id=OuterRef("pk"), user_id=user.pk,
            )
        )
    return projects.annotate(
        star_count=Count("starred_by", distinct=True),
        is_starred=is_starred,
    )
