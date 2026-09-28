from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from main.forms import ProjectForm
from main.models import Achievement, Experience, Project
from main.permissions import can_edit_projects
from main.project_queries import PUBLIC_PROJECT_FIELDS, public_projects, with_star_status


def safe_next_url(request, fallback):
    """Keep login and star redirects on this site, including filtered listings."""
    target = request.POST.get("next") or request.GET.get("next", "")
    if url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return target
    return fallback


def show_main(request):
    last_login = request.COOKIES.get('last_login', 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": "Noe Andrew",
        "npm": "2506621440",
        "study_program": "S1 Sistem Informasi",
        "active_page": "about",
        "bio": (
            "Information Systems at Universitas Indonesia student passionate about software engineering and fintech. Been fortunate enough to win several hackathons and innovation competitions, but I'm equally proud of my wins on the dance floor. Collaborative problem-solver who thrives working with teams on technical challenges."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Noe Andrew",
        "active_page": "experience",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)


def show_achievements(request):
    context = {
        "name": "Noe Andrew",
        "active_page": "achievements",
        "achievement_list": Achievement.objects.all(),
    }
    return render(request, "achievements.html", context)


@require_GET
def get_projects_json(request):
    projects = public_projects(request.GET.get("title", ""))
    return HttpResponse(
        serializers.serialize("json", projects, fields=PUBLIC_PROJECT_FIELDS),
        content_type="application/json",
    )


@require_GET
def get_projects_xml(request):
    projects = public_projects(request.GET.get("title", ""))
    return HttpResponse(
        serializers.serialize("xml", projects, fields=PUBLIC_PROJECT_FIELDS),
        content_type="application/xml",
    )


@require_GET
def show_projects(request):
    # Follow the tutorial's data-delivery exercise: JSON -> model objects -> HTML.
    json_response = get_projects_json(request)
    projects = [
        item.object
        for item in serializers.deserialize("json", json_response.content.decode("utf-8"))
    ]
    # Enrich the deserialized objects in bulk, without loading star-givers' accounts.
    star_rows = with_star_status(
        Project.objects.filter(pk__in=[project.pk for project in projects]), request.user,
    ).values_list("pk", "star_count", "is_starred")
    star_status = {pk: (count, starred) for pk, count, starred in star_rows}
    for project in projects:
        project.star_count, project.is_starred = star_status.get(project.pk, (0, False))
    context = {
        "name": "Noe Andrew",
        "active_page": "projects",
        "project_list": projects,
        "title_query": request.GET.get("title", "").strip(),
        "can_edit_projects": can_edit_projects(request.user),
    }
    return render(request, "project.html", context)


@require_GET
def project_detail(request, project_id):
    project = get_object_or_404(
        with_star_status(Project.objects.all(), request.user), pk=project_id,
    )
    return render(request, "project_detail.html", {
        "name": "Noe Andrew",
        "active_page": "projects",
        "project": project,
        "can_edit_projects": can_edit_projects(request.user),
    })


@login_required(login_url="main:login")
@require_http_methods(["GET", "POST"])
def create_project(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    form = ProjectForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": "Noe Andrew",
        "active_page": "projects",
        "form": form,
        "is_update": False,
        "submit_label": "Tambah Proyek",
    }
    return render(request, "projects_form.html", context)


@login_required(login_url="main:login")
@require_http_methods(["GET", "POST"])
def update_project(request, project_id):
    if not can_edit_projects(request.user):
        raise PermissionDenied
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(
        request.POST if request.method == "POST" else None,
        instance=project,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek berhasil diperbarui!")
        return redirect("main:show_projects")
    return render(request, "projects_form.html", {
        "name": "Noe Andrew",
        "active_page": "projects",
        "form": form,
        "project": project,
        "is_update": True,
        "submit_label": "Simpan Perubahan",
    })


@login_required(login_url="main:login")
@require_http_methods(["GET", "POST"])
def delete_project(request, project_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Proyek berhasil dihapus!")
    return redirect("main:show_projects")

@require_http_methods(["GET", "POST"])
def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Noe Andrew",
        "active_page": "register",
        "form": form,
    }
    return render(request, "register.html", context)

@require_http_methods(["GET", "POST"])
def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)
    next_url = safe_next_url(request, reverse("main:show_main"))

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect(next_url)
        response.set_cookie(
            "last_login", timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
            httponly=True, secure=request.is_secure(), samesite="Lax",
        )
        return response

    context = {
        "name": "Noe Andrew",
        "active_page": "login",
        "form": form,
        "next": next_url,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

@login_required(login_url="main:login")
@require_POST
def toggle_star(request, project_id):
    # Serialize concurrent toggles on databases supporting row locks. The M2M
    # table also enforces one membership per (project, user) at database level.
    with transaction.atomic():
        project = get_object_or_404(Project.objects.select_for_update(), pk=project_id)
        if project.starred_by.filter(pk=request.user.pk).exists():
            project.starred_by.remove(request.user)
        else:
            project.starred_by.add(request.user)

    return redirect(safe_next_url(request, reverse("main:show_projects")))
