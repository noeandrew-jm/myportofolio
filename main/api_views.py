"""Versioned project API using the portfolio's existing sessions and roles."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.achievement_queries import achievements_with_stars
from main.models import Achievement, Project
from main.permissions import IsPortfolioOwnerOrEditorOrReadOnly
from main.serializers import AchievementSerializer, ProjectSerializer


def projects_with_stars():
    # Only usernames and IDs are needed to render the public star metadata.
    return Project.objects.prefetch_related(Prefetch(
        "starred_by", queryset=get_user_model().objects.only("id", "username"),
    )).order_by("title", "id")


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def project_list(request):
    if request.method in ("GET", "HEAD"):
        projects = projects_with_stars()
        title = request.query_params.get("title", "").strip()
        if title:
            projects = projects.filter(title__icontains=title)
        serializer = ProjectSerializer(projects, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = ProjectSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def project_detail(request, project_id):
    project = get_object_or_404(projects_with_stars(), pk=project_id)
    if request.method in ("GET", "HEAD"):
        return Response(ProjectSerializer(project, context={"request": request}).data)

    if request.method == "DELETE":
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProjectSerializer(
        project, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def project_star(request, project_id):
    # Match the existing star action's transaction and row locking on PostgreSQL.
    with transaction.atomic():
        project = get_object_or_404(Project.objects.select_for_update(), pk=project_id)
        if project.starred_by.filter(pk=request.user.pk).exists():
            project.starred_by.remove(request.user)
        else:
            project.starred_by.add(request.user)
        project = projects_with_stars().get(pk=project.pk)
        data = ProjectSerializer(project, context={"request": request}).data
    return Response(data)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def achievement_list(request):
    if request.method in ("GET", "HEAD"):
        achievements = achievements_with_stars(
            request.user, request.query_params.get("title", ""),
        )
        return Response(AchievementSerializer(
            achievements, many=True, context={"request": request},
        ).data)
    serializer = AchievementSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def achievement_detail(request, achievement_id):
    achievement = get_object_or_404(achievements_with_stars(request.user), pk=achievement_id)
    if request.method in ("GET", "HEAD"):
        return Response(AchievementSerializer(achievement, context={"request": request}).data)
    if request.method == "DELETE":
        achievement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = AchievementSerializer(
        achievement, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def achievement_star(request, achievement_id):
    with transaction.atomic():
        achievement = get_object_or_404(
            Achievement.objects.select_for_update(), pk=achievement_id,
        )
        if achievement.starred_by.filter(pk=request.user.pk).exists():
            achievement.starred_by.remove(request.user)
        else:
            achievement.starred_by.add(request.user)
        achievement = achievements_with_stars(request.user).get(pk=achievement.pk)
        data = AchievementSerializer(achievement, context={"request": request}).data
    return Response(data)
