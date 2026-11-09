from django.contrib import admin

from .forms import AchievementForm
from .models import Achievement, Experience, Project
from .permissions import can_create_achievements, can_edit_achievements


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "started_at", "ended_at")
    list_filter = ("category", "ended_at")
    search_fields = ("title", "description")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    form = AchievementForm
    fields = ("title", "description", "award", "thumbnail", "display_order")
    list_display = ("title", "award", "display_order")
    list_editable = ("display_order",)
    search_fields = ("title", "description", "award")

    def has_add_permission(self, request):
        return can_create_achievements(request.user)

    def has_change_permission(self, request, obj=None):
        return can_edit_achievements(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_create_achievements(request.user)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "tech_stack", "project_url")
    search_fields = ("title", "description", "tech_stack")
