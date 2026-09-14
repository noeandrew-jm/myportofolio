from django.shortcuts import render

from main.models import Achievement, Experience


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
