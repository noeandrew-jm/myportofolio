from django.contrib import admin

from .models import Experience


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
	list_display = ("title", "category", "started_at", "ended_at")
	list_filter = ("category", "ended_at")
	search_fields = ("title", "description")
