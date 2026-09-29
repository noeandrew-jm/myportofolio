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
| Daftar AJAX (Tutorial 05) | `show_projects` merender kerangka; `projects.js` mengambil JSON lalu membangun kartu melalui DOM dan `textContent` |
| Pencarian AJAX | Debounce 300 ms, Enter langsung mencari, pembatalan permintaan lama, Reset dan Coba Lagi |
| Tambah AJAX | Modal khusus superuser, POST `/projects/add-ajax/`, `ProjectForm`, CSRF, status 201/400/403, penyegaran daftar tanpa reload |
| Toast | Komponen global dengan pesan teks aman, tipe sukses/error/normal, timer dan tombol tutup |
| XSS | `textContent`, URL HTTP/HTTPS pada kartu dan detail, serta pembersihan tag HTML di `ProjectForm` |
| Antarmuka | Tambah Proyek, Edit Proyek, Hapus Proyek dan validasi form |
| Tampilan data | Kartu bergeser; URL gambar dan proyek opsional; empty state untuk hasil kosong |

`id` adalah UUID otomatis dan tidak muncul sebagai input form. Model ini tidak
memiliki field timestamp. URL divalidasi oleh Django; data teks di template
di-escape otomatis, sedangkan kartu AJAX menggunakan `textContent`. POST yang tidak valid tidak menulis perubahan ke database.

## Audit Tutorial 05 — 29 September 2026

Audit mengikuti lampiran JavaScript/AJAX; contoh kode disesuaikan dengan desain
dan aturan akses portofolio yang sudah ada.

| Ketentuan lampiran | Hasil pemeriksaan |
| --- | --- |
| Berkas sensitif dan environment tidak dilacak | `.env*`, `db.sqlite3`, `env/`, dan `.venv/` ada di `.gitignore`; tidak ada berkas tersebut yang dilacak Git |
| Toast global, animasi, tiga tipe, durasi dan pembatalan timer | Komponen dimuat di `base.html`, memakai Popover API dan `textContent` |
| JSON proyek dan metadata star pengguna aktif | UUID, lima field proyek, `star_count`, serta `is_starred`; GET mendukung filter judul tanpa membedakan kapital |
| Halaman daftar berupa kerangka AJAX | Tidak ada `project_list` pada context; kartu dibentuk setelah GET JSON |
| Loading, error, kosong dan data tersedia | Keempat state terpisah; tombol Coba Lagi memuat ulang data tanpa reload halaman |
| Pencarian, debounce dan pembatalan respons lama | Jeda 300 ms, Enter langsung mencari, `AbortController` dan pemeriksaan request aktif; query awal URL tetap dibaca |
| Modal tambah hanya untuk superuser | `ProjectForm`, label, CSRF, tutup/Batal/Escape, fokus keyboard dan layout mobile |
| Endpoint tambah hanya menerima POST | GET ditolak 405; akun biasa/anonim ditolak JSON 403; input tidak valid 400; berhasil 201 |
| Tambah tanpa reload | `FormData` dan header `X-CSRFToken`; tombol dikunci saat request; daftar diperbarui dengan filter aktif |
| Penanganan kegagalan tambah | Error field/toast tampil; draft tetap; tombol aktif kembali; HTML/non-JSON tidak dianggap sukses |
| Perlindungan XSS data baru dan lama | Teks DOM aman, skema URL disaring, `clean_title`, `clean_tech_stack`, dan `clean_description` memakai `strip_tags` |
| Fitur sebelumnya tetap berjalan | Detail, star/unstar, edit Editor/superuser, hapus superuser, dan carousel tetap diperiksa |

Penyesuaian terhadap contoh: identitas `starred_by_names` tidak dipublikasikan
karena aturan API Tugas 4 yang sudah diterapkan melarang identitas pemberi star.
Jumlah dan status star tetap tersedia. `textContent` digunakan sebagai alternatif
`escapeHtml` yang disebutkan dalam tutorial. JavaScript dan CSS dipisahkan ke
berkas statis; token CSRF diambil dari input Django. Tombol uji toast sementara
tidak diperlukan karena toast dipakai langsung oleh alur tambah proyek.

Commit, push, deployment PWS, dan pengumpulan SCELE tidak termasuk hasil
pemeriksaan lokal ini.

Verifikasi audit: **96 tes Django dan 7 skenario Selenium Chrome lulus**;
`manage.py check`, `makemigrations --check --dry-run`, pemeriksaan sintaks
JavaScript, dan `git diff --check` juga lulus. Browser memakai database
sementara; screenshot modal desktop dan mobile 390 px diperiksa.

## Menjalankan dan memeriksa

```powershell
python manage.py migrate
python manage.py runserver
python manage.py check
python manage.py test main
python test_e2e.py --headless
```

Jika memakai virtual environment repo, jalankan perintah lewat
`.\env\Scripts\python.exe`. Aset frontend hasil build sudah disertakan; Node
tidak dibutuhkan untuk menjalankan Django. Untuk membangun ulang setelah
mengubah `frontend/`, jalankan `npm.cmd run build`.
