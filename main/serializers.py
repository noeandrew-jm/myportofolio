from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.html import strip_tags
from rest_framework import serializers

from main.achievement_urls import clean_achievement_thumbnail, safe_achievement_thumbnail
from main.models import Achievement, Project
from main.project_urls import validate_web_url


class ProjectSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "title", "description", "tech_stack",
            "project_url", "project_image_url",
            "star_count", "is_starred", "starred_by_names",
        ]
        read_only_fields = ["id"]

    def validate_title(self, value):
        return self._clean_required_text(value)

    def validate_description(self, value):
        return self._clean_required_text(value)

    def validate_tech_stack(self, value):
        return self._clean_required_text(value)

    def _clean_required_text(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("This field cannot be empty or contain only HTML tags.")
        return value

    def validate_project_url(self, value):
        return self._clean_web_url(value)

    def validate_project_image_url(self, value):
        return self._clean_web_url(value)

    def _clean_web_url(self, value):
        # Match ProjectForm, preserving literal ampersands in query strings.
        value = strip_tags(value.replace("&", "&amp;")).replace("&amp;", "&").strip()
        if value:
            try:
                validate_web_url(value)
            except DjangoValidationError as error:
                raise serializers.ValidationError(error.messages) from error
        return value

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()

    def get_starred_by_names(self, obj):
        return ", ".join(sorted(user.username for user in obj.starred_by.all()))


class AchievementSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = [
            "id", "title", "description", "award", "thumbnail", "display_order",
            "star_count", "is_starred",
        ]
        read_only_fields = ["id", "star_count", "is_starred"]

    def validate_title(self, value):
        return self._clean_required_text(value)

    def validate_description(self, value):
        return self._clean_required_text(value)

    def validate_award(self, value):
        return strip_tags(value).strip()

    def validate_thumbnail(self, value):
        try:
            return clean_achievement_thumbnail(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        except ValueError as error:
            raise serializers.ValidationError("Alamat gambar tidak valid.") from error

    def _clean_required_text(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Teks wajib tidak boleh kosong atau hanya berisi tag HTML.")
        return value

    def get_star_count(self, obj):
        if hasattr(obj, "star_count"):
            return obj.star_count
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        if hasattr(obj, "is_starred"):
            return obj.is_starred
        return obj.starred_by.filter(pk=request.user.pk).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Old database rows must not turn into unsafe image sources in clients.
        data["thumbnail"] = safe_achievement_thumbnail(instance.thumbnail)
        return data
