from django.contrib import admin

from .models import Achievement, Experience


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "started_at", "ended_at")
    list_filter = ("category", "ended_at")
    search_fields = ("title", "description")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "award", "display_order")
    list_editable = ("display_order",)
    search_fields = ("title", "description", "award")
