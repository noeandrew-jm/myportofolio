"""URL checks for project data rendered outside ModelForm validation."""

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


validate_web_url = URLValidator(schemes=["http", "https"])


def safe_project_url(value):
    """Keep legacy database values from becoming executable links or images."""
    if not value:
        return ""
    try:
        validate_web_url(value)
    except ValidationError:
        return ""
    return value
