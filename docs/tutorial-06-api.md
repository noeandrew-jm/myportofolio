# Tutorial 06: Django REST Framework pada Projects

Bagian pilihan Tugas 3–5 pada repositori ini adalah **Projects**. Implementasi
melanjutkan model, data, desain kartu, modal, dan form edit yang sudah ada.
Experience, Achievements, profil, serta endpoint lama tetap tersedia.

## Endpoint dan peran

| Endpoint | Method | Akses dan hasil |
| --- | --- | --- |
| `/api/v1/projects/` | GET, HEAD | Publik; daftar, filter `?title=...`, urutan judul lalu UUID |
| `/api/v1/projects/` | POST | Superuser; 201 atau validasi 400 |
| `/api/v1/projects/<uuid>/` | GET, HEAD | Publik; objek atau 404 |
| `/api/v1/projects/<uuid>/` | PUT, PATCH | Superuser atau grup `Editor`; 200 atau validasi 400 |
| `/api/v1/projects/<uuid>/` | DELETE | Superuser; 204 dengan body kosong |
| `/api/v1/projects/<uuid>/star/` | POST | Akun login; toggle akun peminta, 200 |
| `/api-auth/login/` | GET, POST | Login Browsable API; login portofolio juga dapat dipakai |

OPTIONS tersedia melalui DRF; safe methods tidak mengubah data. Endpoint star
tetap membutuhkan login, termasuk untuk OPTIONS. Dengan SessionAuthentication,
aksi yang membutuhkan login ditolak dengan 403 bagi pengunjung anonim; GET star
oleh akun login menghasilkan 405. Pencarian tanpa hasil menghasilkan `[]`, 200.

**Penyesuaian dari contoh tutorial:** kelas `IsPortfolioOwnerOrReadOnly` tetap
tersedia, tetapi daftar/detail Projects menggunakan
`IsPortfolioOwnerOrEditorOrReadOnly`. Ini mengikuti bagian **Implementasi Peran
Editor** di lampiran dan mempertahankan hak edit Projects dari tugas sebelumnya.
Tes contoh yang menolak Editor diubah menjadi penolakan akun staff biasa,
ditambah tes bahwa Editor boleh PUT/PATCH tetapi tidak boleh create/delete.
`is_staff` saja tidak memberikan hak mengelola konten.

## Serializer, validasi, dan AJAX

`ProjectSerializer` menghasilkan objek datar: `id`, `title`, `description`,
`tech_stack`, `project_url`, `project_image_url`, `star_count`, `is_starred`, dan
`starred_by_names`. UUID dan ketiga field star hanya dapat dibaca. Klien tidak
dapat memilih akun pemberi star atau mengirim relasi `starred_by`. API v1
menampilkan username pemberi star sesuai lampiran; email, password, dan data
akun lain tidak disertakan. JSON/XML lama mempertahankan kontraknya sendiri.

Teks dibersihkan dari tag HTML dan spasi tepi. Ketiga field teks wajib tidak
boleh kosong sesudah pembersihan. Kedua URL opsional dan hanya menerima HTTP
atau HTTPS, mengikuti `ProjectForm`. PUT membutuhkan semua field wajib; PATCH
hanya mengubah field yang dikirim. Field opsional yang tidak dikirim pada update
tetap mempertahankan nilai lama.

`project.html` memasang URL hasil `{% url %}` ke atribut `data-*`. Karena itu
`static/js/projects.js` tetap dapat dipakai sebagai berkas statis tanpa tag
template mentah. Kartu membaca `project.id` dan `project.title`, menggunakan DOM
dan `textContent`, serta memeriksa skema URL untuk data lama dari admin/shell.
Tidak ada duplikasi script inline.

Daftar/pencarian memakai GET; modal tambah mengirim lima field dalam JSON lewat
POST; star menggunakan POST; konfirmasi hapus mengirim DELETE. Semua aksi AJAX
meminta `application/json`, mengirim token CSRF untuk penulisan, dan memperbarui
daftar tanpa memuat ulang dokumen. Respons 204 tidak dibaca sebagai JSON.
Error DRF tampil di form/toast, input gagal tetap tersedia, dan filter aktif
dipertahankan. Debounce 300 ms, pembatalan hasil pencarian lama, serta penguncian
tombol selama request tetap berlaku. Toggle tidak diulang otomatis.

CSRF dirender juga bagi pengguna biasa di halaman Projects sehingga cookie
yang hilang dibuat kembali. Tidak ada `csrf_exempt` baru. Form edit klasik
tetap digunakan oleh Editor/superuser.

## Menjalankan dan memeriksa

Jalankan dari direktori `manage.py` pada PowerShell:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements.txt
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py migrate
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py test main.tests_api --verbosity 2
.\env\Scripts\python.exe manage.py test main contacts --verbosity 1
.\env\Scripts\python.exe -m pip install -r requirements-dev.txt
.\env\Scripts\python.exe test_e2e.py --headless
.\env\Scripts\python.exe manage.py collectstatic --noinput
.\env\Scripts\python.exe manage.py runserver
```

Tidak ada perubahan model yang membutuhkan migrasi baru. File test berada di
`main/tests_api.py`, bukan `main/migrations/`. Tes menggunakan database sementara.
Selenium membuat akun uji sendiri dan tidak memerlukan password akun portofolio.

Percobaan serializer tanpa menyimpan data:

```powershell
.\env\Scripts\python.exe manage.py shell
```

```python
from main.models import Project
from main.serializers import ProjectSerializer

print(ProjectSerializer(Project.objects.prefetch_related("starred_by"), many=True).data)
candidate = ProjectSerializer(data={
    "title": "Portfolio", "description": "My website", "tech_stack": "Django",
})
print(candidate.is_valid())  # True
print(candidate.validated_data)
invalid = ProjectSerializer(data={"title": ""})
print(invalid.is_valid())  # False
print(invalid.errors)
exit()
```

Buka `http://127.0.0.1:8000/api/v1/projects/` untuk Browsable API atau tambahkan
`?format=json` untuk JSON. Di `/projects/`, periksa Network: daftar memakai
`/api/v1/projects/`, tambah POST 201, star POST 200, dan hapus DELETE 204.
Coba pencarian kosong, validasi gagal, dan keempat peran. Gunakan proyek uji
untuk mencoba hapus. Halaman profil, Experience, dan Achievements juga harus
tetap dapat dibuka.

## Urutan commit Git

Perintah berikut adalah langkah untuk dijalankan pemilik setelah meninjau diff.
Sesi implementasi tidak menjalankan commit, push, atau deploy. Branch saat
implementasi adalah `master`; remote yang tersedia adalah `origin` dan `pws`.
Jangan gunakan `git add .` agar perubahan pribadi lain tidak ikut tanpa ditinjau.

1. Tinjau dan commit API beserta tes backend:

   ```powershell
   git status --short
   git diff --check
   git diff
   git add requirements.txt portofolio/settings.py portofolio/urls.py main/permissions.py main/serializers.py main/api_views.py main/api_urls.py main/tests_api.py
   git diff --cached --stat
   git diff --cached
   git commit -m "feat(api): add DRF project CRUD, stars, and Editor permissions"
   ```

2. Commit integrasi antarmuka dan tes browser:

   ```powershell
   git add .gitignore templates/project.html templates/components/project_form_modal.html static/js/projects.js main/test_ajax.py main/test_projects.py e2e/browser_checks.py
   git diff --cached --stat
   git diff --cached
   git commit -m "feat(projects): integrate DRF AJAX create, star, and delete"
   ```

3. Commit panduan dan hasil verifikasi:

   ```powershell
   git add README.md docs/tutorial-06-api.md docs/task-checklist.md docs/ai-log.md
   git diff --cached --stat
   git commit -m "docs: document DRF verification, Git commits, and PWS deployment"
   git status --short
   git log -3 --oneline
   ```

Perubahan whitespace yang sudah ada di `static/js/toast.js` tidak diperlukan
untuk API dan tidak otomatis dimasukkan ke daftar staging di atas. File kosong
`main/migrations/tests_api.py` sebelumnya belum dilacak Git dan sudah dibuang;
tidak perlu `git rm` untuk file tersebut. Bila ada file lain yang sudah di-stage,
tinjau lebih dulu sebelum menjalankan commit.

Cache unduhan Selenium juga diabaikan agar driver lokal baru tidak ikut
di-commit. Berkas driver yang sudah dilacak pada versi sebelumnya tidak dihapus.

Setelah pemilik menyetujui push GitHub:

```powershell
git push origin master
git rev-parse HEAD
```

Tautan pengumpulan adalah
`https://github.com/noeandrew-jm/myportofolio/commit/<HASH_DARI_GIT_REV_PARSE>`.
Periksa status publik repositori dan kirim tautan commit melalui SCELE. Tenggat
tidak tercantum pada lampiran yang diterima, jadi periksa jadwal di SCELE.

## PWS setelah persetujuan pemilik

1. Tinjau tujuan remote `pws` di komputer sendiri; jangan membagikan URL yang
   mengandung token/password. Pastikan target adalah aplikasi portofolio ini.
2. Setelah commit lokal dan push GitHub selesai serta deploy disetujui, gunakan
   alur Tutorial 01. Jika remote PWS mengharapkan branch `master`:

   ```powershell
   git push pws master:master
   ```

3. Periksa build/log PWS: dependency `djangorestframework==3.18.3` terpasang,
   migrasi sukses, dan `collectstatic --noinput` menyertakan aset DRF serta
   `projects.js` terbaru. Konfigurasi Environs tetap mengikuti
   [panduan database PWS](pws-database.md).
4. `CSRF_TRUSTED_ORIGINS` sudah mencakup
   `https://noe-andrew-myportofolio.pws.cs.ui.ac.id`. Bila hostname deployment
   berbeda, sesuaikan origin HTTPS dan `ALLOWED_HOSTS` terlebih dahulu.
5. Periksa GET API publik dan login melalui HTTPS. Sebagai superuser buat satu
   proyek uji, ubah, lalu hapus; sebagai akun biasa coba star. Pastikan operasi
   tanpa izin atau tanpa CSRF ditolak. Jangan menuliskan password pada kode,
   README, chat, atau pesan commit; login langsung melalui browser bila perlu.

Deployment, status publik GitHub, tautan commit, dan pengumpulan belum dapat
dibuktikan hanya dari tes lokal. `.env*`, `env/`, dan database lokal sudah
diabaikan melalui `.gitignore`.

## Hasil verifikasi lokal — 4 November 2026

- `manage.py test main.tests_api --verbosity 2`: 24 tes API/serializer lulus.
- `manage.py test main contacts --verbosity 1 --noinput`: 127 tes lulus,
  termasuk tes API dan regresi fitur lama.
- Selenium Chrome 156: 10 skenario terverifikasi. Sembilan lulus pada suite
  lengkap; satu skenario tambah/star/hapus lulus pada pengujian ulang terarah
  setelah pencatat request di tes diperbaiki karena menghitung dua kali.
- Pemeriksaan sistem, rencana migrasi, dependency (`pip check`), sintaks
  JavaScript, dan `git diff --check` bersih. Tidak ada migrasi tertunda maupun
  perubahan model. `collectstatic --noinput` berhasil, termasuk aset DRF.
- Percobaan shell serializer berhasil membaca data tanpa menyimpan; kandidat
  valid menghasilkan True, judul kosong menghasilkan False dengan error field.
- Eksperimen permission dijalankan melalui patch dalam memori: tes penolakan
  pengguna biasa gagal sebagaimana diharapkan saat izin tulis dilonggarkan.
  Patch dipulihkan otomatis; tes yang sama kembali lulus. Kode eksperimen tidak
  disimpan pada implementasi.
- Screenshot modal desktop dan mobile diperiksa; dialog, fokus, dan toast tetap
  berada dalam viewport. Chrome membutuhkan izin di luar sandbox agar bisa
  mulai; server uji tetap loopback dan database sementara.

Hasil ini membuktikan kondisi lokal yang diuji. Commit/push, deployment PWS,
pemeriksaan produksi, dan pengumpulan SCELE belum dilakukan.

## Acuan

- [DRF serializers dan validasi](https://www.django-rest-framework.org/api-guide/serializers/)
- [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/)
- [SessionAuthentication dan CSRF](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication)
- [DRF testing](https://www.django-rest-framework.org/api-guide/testing/)
