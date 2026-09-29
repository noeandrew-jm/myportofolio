from django.core.exceptions import ValidationError
from django.forms import ModelForm, TextInput, Textarea, URLInput
from django.utils.html import strip_tags

from main.models import Project


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
