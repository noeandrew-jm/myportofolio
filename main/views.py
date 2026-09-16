from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from main.forms import ProjectForm
from main.models import Achievement, Experience, Project


def show_main(request):
    context = {
        "name": "Noe Andrew",
        "npm": "2506621440",
        "study_program": "S1 Sistem Informasi",
        "active_page": "about",
        "bio": (
            "Information Systems at Universitas Indonesia student passionate about software engineering and fintech. Been fortunate enough to win several hackathons and innovation competitions, but I'm equally proud of my wins on the dance floor. Collaborative problem-solver who thrives working with teams on technical challenges."
        ),
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
def create_project(request):
    form = ProjectForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": "Noe Andrew",
        "active_page": "projects",
        "form": form,
    }
    return render(request, "projects_form.html", context)


@require_http_methods(["GET", "POST"])
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Proyek berhasil dihapus!")
    return redirect("main:show_projects")
