from django.core.exceptions import ValidationError
from django.forms import ModelForm, NumberInput, TextInput, Textarea, URLInput
from django.utils.html import strip_tags

from main.achievement_urls import clean_achievement_thumbnail
from main.models import Achievement, Project
from main.project_urls import validate_web_url


class ProjectForm(ModelForm):
    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Nama proyek tidak boleh hanya berisi tag HTML.")
        return title

    def clean_tech_stack(self):
        tech_stack = strip_tags(self.cleaned_data["tech_stack"]).strip()
        self.fields["tech_stack"].validate(tech_stack)
        return tech_stack

    def clean_description(self):
        description = strip_tags(self.cleaned_data["description"]).strip()
        self.fields["description"].validate(description)
        return description

    def clean_project_url(self):
        return self._clean_web_url(self.cleaned_data["project_url"])

    def clean_project_image_url(self):
        return self._clean_web_url(self.cleaned_data["project_image_url"])

    def _clean_web_url(self, value):
        # Keep URL query ampersands literal while the HTML parser removes tags.
        value = strip_tags(value.replace("&", "&amp;")).replace("&amp;", "&").strip()
        if value:
            validate_web_url(value)
        return value

    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "tech_stack",
            "project_url",
            "project_image_url",
        ]

        labels = {
            "title": "Nama Proyek",
            "description": "Deskripsi Proyek",
            "tech_stack": "Teknologi yang Digunakan",
            "project_url": "URL Proyek",
            "project_image_url": "URL Gambar Proyek",
            
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan Proyekmu",
                    "rows": 3,
                }
            ),
            "tech_stack": TextInput(
                attrs={
                    "placeholder": "Django, Python, HTML, CSS",
                }
            ),
            "project_url": URLInput(
                attrs={
                    "placeholder": "https://github.com/noeandrew-jm/myportofolio",
                }
            ),
            "project_image_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }

        help_texts = {
            "project_url": "Opsional. Masukkan URL lengkap dengan https://.",
            "project_image_url": (
                "Opsional. Untuk Google Drive, gunakan URL thumbnail dan atur "
                "akses gambar menjadi Anyone with the link (Viewer)."
            ),
        }


class AchievementForm(ModelForm):
    def clean_title(self):
        return self._clean_required_text("title")

    def clean_description(self):
        return self._clean_required_text("description")

    def clean_award(self):
        return strip_tags(self.cleaned_data["award"]).strip()

    def clean_thumbnail(self):
        try:
            return clean_achievement_thumbnail(self.cleaned_data["thumbnail"])
        except ValueError as error:
            raise ValidationError("Alamat gambar tidak valid.") from error

    def _clean_required_text(self, field):
        value = strip_tags(self.cleaned_data[field]).strip()
        self.fields[field].validate(value)
        return value

    class Meta:
        model = Achievement
        fields = ["title", "description", "award", "thumbnail", "display_order"]
        labels = {
            "title": "Nama Prestasi",
            "description": "Deskripsi",
            "award": "Penghargaan",
            "thumbnail": "Gambar Prestasi",
            "display_order": "Urutan Tampilan",
        }
        widgets = {
            "title": TextInput(attrs={"maxlength": 255}),
            "description": Textarea(attrs={"rows": 4}),
            "award": TextInput(attrs={"maxlength": 100}),
            "thumbnail": TextInput(attrs={"placeholder": "https://... atau /static/image/..."}),
            "display_order": NumberInput(attrs={"min": 0}),
        }
        help_texts = {"thumbnail": "Opsional. Gunakan URL HTTP/HTTPS atau path gambar /static/."}
