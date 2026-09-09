from django.shortcuts import render

from main.models import Experience


def landing_page(request):
    return render(request, "index.html")


def achievements_page(request):
    return render(request, "achievements.html")


def experience_page(request):
    context = {
        "name": "Noe Andrew",
        "experience_list": Experience.objects.order_by("-started_at"),
    }
    return render(request, "experience.html", context)
