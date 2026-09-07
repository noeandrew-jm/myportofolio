from django.shortcuts import render


def landing_page(request):
    return render(request, "index.html")


def achievements_page(request):
    return render(request, "achievements.html")


def experience_page(request):
    return render(request, "experience.html")
