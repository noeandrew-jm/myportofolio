from django.urls import path

from main.views import show_achievements, show_experience, show_main

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("achievements/", show_achievements, name="show_achievements"),
    path("experience/", show_experience, name="show_experience"),
]