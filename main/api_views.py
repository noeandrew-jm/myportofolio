"""HTTP adapters for portfolio resources: permissions, validation, and responses.

Read queries and shared mutations live in their own modules. Keep authentication
and permission decorators on each function so every entry point enforces the
same policy, including requests sent without the portfolio's HTML interface.
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.achievement_queries import achievements_with_stars
from main.models import Achievement, Project
from main.permissions import IsPortfolioOwnerOrEditorOrReadOnly
from main.project_queries import projects_with_stars
from main.serializers import AchievementSerializer, ProjectSerializer
from main.services import toggle_content_star


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def project_list(request):
    if request.method in ("GET", "HEAD"):
        projects = projects_with_stars(request.query_params.get("title", ""))
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
    # Read a fresh relation while the mutation's row lock is still held.
    with transaction.atomic():
        project = toggle_content_star(Project, project_id, request.user)
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
    # Annotation values are snapshots: reload them after changing membership.
    with transaction.atomic():
        achievement = toggle_content_star(Achievement, achievement_id, request.user)
        achievement = achievements_with_stars(request.user).get(pk=achievement.pk)
        data = AchievementSerializer(achievement, context={"request": request}).data
    return Response(data)
