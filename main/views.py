from django.contrib.auth.decorators import login_required  # Tambahkan baris ini
from django.core.exceptions import PermissionDenied        # Tambahkan baris ini
from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
import datetime

from main.forms import ProjectForm
from main.models import Achievement, Experience, Project


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
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.all()
    if title_query:
        projects = projects.filter(title__icontains=title_query)
    
    return HttpResponse(
        serializers.serialize("json", projects), content_type="application/json"
    )
    projects_json = serializers.serialize(
        "json", projects, use_natural_foreign_keys=True  # Tambahkan argumen ini
)


@require_GET
def get_projects_xml(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.all()
    if title_query:
        projects = projects.filter(title__icontains=title_query)

    return HttpResponse(
        serializers.serialize("xml", projects), content_type="application/xml"
    )


@require_GET
def show_projects(request):
    # Follow the tutorial's data-delivery exercise: JSON -> model objects -> HTML.
    json_response = get_projects_json(request)
    projects = serializers.deserialize("json", json_response.content.decode("utf-8"))
    context = {
        "name": "Noe Andrew",
        "active_page": "projects",
        "project_list": [project.object for project in projects],
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "project.html", context)


@require_http_methods(["GET", "POST"])
@login_required(login_url="/login/")  
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


@require_http_methods(["GET", "POST"])
def update_project(request, project_id):
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


@require_http_methods(["GET", "POST"])
@login_required(login_url="/login/")  
def delete_project(request, project_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Proyek berhasil dihapus!")
    return redirect("main:show_projects")

def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Noe Andrew",
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "Noe Andrew",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

# Tanpa cek is_superuser: semua akun yang sudah login boleh memberi star
@login_required(login_url="/login/")
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        # Kalau akun ini sudah pernah memberi star, batalkan star-nya.
        # Kalau belum, tambahkan star.
        if request.user in project.starred_by.all():
            project.starred_by.remove(request.user)
        else:
            project.starred_by.add(request.user)

    return redirect("main:show_projects")
