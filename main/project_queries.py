"""Public project data and aggregate stars, without exposing account records."""

from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from main.models import Project


# Keep the tutorial's Django serializer shape, but never serialize user relations.
PUBLIC_PROJECT_FIELDS = (
    "title", "description", "tech_stack", "project_url", "project_image_url",
)


def public_projects(title_query=""):
    projects = Project.objects.all()
    if title_query.strip():
        projects = projects.filter(title__icontains=title_query.strip())
    return projects


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
