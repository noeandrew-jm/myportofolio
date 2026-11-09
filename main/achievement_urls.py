"""Accept public web images and the portfolio's existing static image paths."""

from urllib.parse import unquote, urlsplit

from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from main.project_urls import validate_web_url


def validate_achievement_thumbnail(value):
    if not value:
        return
    if value.startswith("/static/"):
        path = unquote(urlsplit(value).path)
        if (
            path.startswith("/static/") and len(path) > len("/static/")
            and not any(part in (".", "..") for part in path.split("/"))
            and "\\" not in path and not any(ord(char) < 32 for char in value + path)
        ):
            return
        raise ValidationError("Gunakan path /static/ yang valid tanpa traversal direktori.")
    validate_web_url(value)


def clean_achievement_thumbnail(value):
    value = strip_tags(value.replace("&", "&amp;")).replace("&amp;", "&").strip()
    validate_achievement_thumbnail(value)
    return value


def safe_achievement_thumbnail(value):
    try:
        validate_achievement_thumbnail(value)
    except (ValidationError, ValueError):
        return ""
    return value or ""
