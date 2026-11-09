"""Achievement lists with public, viewer-specific star metadata."""

from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from main.models import Achievement


def achievements_with_stars(user, title=""):
    """Return ordered content with one SQL query and no loaded account records.

    ``Exists`` computes this viewer's membership independently of the aggregate
    star count. Explicit ordering is necessary because aggregation can suppress
    a model's default ordering. Keep this queryset scoped to the current viewer.
    """
    is_starred = Value(False, output_field=BooleanField())
    if user.is_authenticated:
        is_starred = Exists(Achievement.starred_by.through.objects.filter(
            achievement_id=OuterRef("pk"), user_id=user.pk,
        ))
    achievements = Achievement.objects.annotate(
        star_count=Count("starred_by", distinct=True), is_starred=is_starred,
    ).order_by("display_order", "title", "id")
    title = title.strip()
    if title:
        achievements = achievements.filter(title__icontains=title)
    return achievements
