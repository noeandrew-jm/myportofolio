# Checklist tugas — Projects

Bagian data yang dipilih adalah **Projects**. Implementasi mempertahankan data
yang sudah ada dan tidak memerlukan perubahan skema database.

| Persyaratan | Implementasi |
| --- | --- |
| Root template | `templates/base.html`; halaman kartu memakai `showcase_base.html` yang extend root; form tambah/edit memakai satu `projects_form.html` |
| ModelForm | `main/forms.py`: `ProjectForm`, seluruh field editable selain UUID `id` |
| Minimal tiga field dan tipe bervariasi | `title` dan `tech_stack`: `CharField`; `description`: `TextField`; `project_url` dan `project_image_url`: `URLField` |
| Create | `create_project`, GET/POST `/projects/add/` |
| Update | `update_project`, GET/POST `/projects/<uuid>/edit/`, form terisi data lama |
| Delete | `delete_project`, POST `/projects/<uuid>/delete/`, konfirmasi dan CSRF |
| JSON | `get_projects_json`, GET `/api/projects/`, pencarian judul opsional `?title=...` |
| JSON → deserialisasi → HTML | `show_projects` mengambil hasil `get_projects_json`, memanggil `serializers.deserialize`, lalu merender `project.html` |
| Antarmuka | Tambah Proyek, Edit Proyek, Hapus Proyek dan validasi form |
| Tampilan data | Kartu bergeser; URL gambar dan proyek opsional; empty state untuk hasil kosong |

`id` adalah UUID otomatis dan tidak muncul sebagai input form. Model ini tidak
memiliki field timestamp. URL divalidasi oleh Django; data teks di template
di-escape otomatis. POST yang tidak valid tidak menulis perubahan ke database.

## Menjalankan dan memeriksa

```powershell
python manage.py migrate
python manage.py runserver
python manage.py check
python manage.py test main
```

Jika memakai virtual environment repo, jalankan perintah lewat
`.\env\Scripts\python.exe`. Aset frontend hasil build sudah disertakan; Node
tidak dibutuhkan untuk menjalankan Django. Untuk membangun ulang setelah
mengubah `frontend/`, jalankan `npm.cmd run build`.
