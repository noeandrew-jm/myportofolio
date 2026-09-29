# Portofolio Noe Andrew

Website portofolio pribadi untuk Proyek Individu PBP, dibangun bertahap menggunakan Django 5.2, HTML5, dan CSS3. Profil dan tiga focus areas ada di halaman utama; pengalaman, prestasi, dan proyek ditampilkan dari database pada halaman terpisah.

Nama : Noe Andrew JM Silalahi

NPM : 2506621440

Kelas : PBP C

## Menjalankan proyek lokal (Windows / PowerShell)

Jalankan perintah dari folder yang berisi `manage.py`. Proyek ini diuji dengan Python 3.14 dan dependency pada `requirements.txt`.

Untuk instalasi pertama:

```powershell
git clone https://github.com/noeandrew-jm/myportofolio.git
cd myportofolio
py -m venv env
.\env\Scripts\python.exe -m pip install -r requirements.txt
```

Jika proyek dan folder `env` sudah tersedia, lewati langkah clone dan pembuatan environment. Buat berkas `.env` di sebelah `manage.py` dengan isi berikut, atau pastikan nilai yang sudah ada sama:

```dotenv
PRODUCTION=False
```

Kemudian jalankan:

```powershell
.\env\Scripts\python.exe manage.py migrate
.\env\Scripts\python.exe manage.py collectstatic --noinput
.\env\Scripts\python.exe manage.py runserver
```

Buka <http://127.0.0.1:8000/>. Biarkan terminal server tetap berjalan; tekan `Ctrl+C` untuk menghentikannya. Penggunaan path Python secara langsung membuat aktivasi environment tidak wajib. Jika environment sudah aktif, perintah yang sama dapat ditulis sebagai `python manage.py ...`.

## Halaman dan pengelolaan konten

| URL | Isi | Sumber data |
| --- | --- | --- |
| `/` | Profil, kontak, dan tiga focus areas | Context profil di `main/views.py`; focus areas statis |
| `/experience/` | Daftar pengalaman, kategori, dan status | Model `Experience` |
| `/achievements/` | Daftar prestasi, penghargaan, dan gambar | Model `Achievement` |
| `/projects/` | Daftar proyek dan pencarian `?title=...` | Model `Project`, dimuat dengan AJAX dari JSON |
| `/projects/<uuid>/` | Detail proyek, jumlah star, dan status star pengguna | Publik; model `Project` |
| `/projects/add/` | Form tambah proyek | Superuser; `ProjectForm` dengan validasi dan CSRF |
| `/projects/add-ajax/` | Tambah proyek dari modal tanpa reload | Superuser; POST dengan `ProjectForm` dan CSRF; respons JSON |
| `/projects/<uuid>/edit/` | Form ubah proyek | Anggota grup `Editor` atau superuser; `ProjectForm` dan CSRF |
| `/projects/<uuid>/delete/` | Hapus proyek lewat konfirmasi | Superuser; POST dengan CSRF; GET tidak menghapus |
| `/projects/<uuid>/star/` | Memberi atau membatalkan star | Pengguna login; hanya POST dengan CSRF |
| `/api/projects/` | Data proyek berformat JSON, filter `?title=...` | Publik; field proyek, jumlah star, dan status star pengguna |
| `/api/projects/xml/` | Percobaan format XML, filter `?title=...` | Publik; field proyek tanpa relasi akun atau metadata star |
| `/register/`, `/login/`, `/logout/` | Registrasi, login, dan logout | Autentikasi dan sesi bawaan Django |
| `/admin/` | Pengelolaan pengalaman, prestasi, dan proyek | Django admin; perlu login |

`migrate` membuat tabel dan memasukkan dua pengalaman serta dua prestasi awal dari konten portofolio yang sudah ada. Migrasi data hanya dijalankan sekali; perubahan selanjutnya bisa dilakukan melalui admin. Database lokal tidak disertakan di Git.

Pengalaman LANJUT.ID ditambahkan lewat migrasi baru `0006_seed_lanjut_experience`. Mengedit `0002_seed_experiences.py` yang sudah diterapkan tidak memasukkan data baru ke database; jalankan `python manage.py migrate` untuk menerapkan migrasi baru. Untuk menambah atau mengedit pengalaman berikutnya, gunakan `/admin/main/experience/`. Migrasi LANJUT.ID mempertahankan entri dengan judul yang sama jika sudah ada. Saat deploy ke PWS, sertakan migrasi baru dan `static/image/Lanjut.id.png`, lalu pastikan migrasi dan `collectstatic --noinput` berhasil di lingkungan produksi.

Untuk membuat akun admin milik sendiri:

```powershell
.\env\Scripts\python.exe manage.py createsuperuser
```

Model `Achievement` memiliki UUID sebagai primary key, serta `title`, `description`, `award`, `thumbnail`, dan `display_order`. `thumbnail` memakai `CharField` karena menyimpan alamat gambar, termasuk path lokal seperti `/static/image/PKM.jpeg`; field ini bukan upload berkas. `award` dan `thumbnail` boleh kosong. Urutan tampilan mengikuti `display_order`, lalu judul dan ID.

`templates/base.html` memuat kerangka HTML, CSS, navbar, pesan Django, dan footer bersama. Isi tiap halaman ada di `index.html`, `experience.html`, `achievements.html`, `project.html`, dan `projects_form.html`. Template turunan menggunakan `block title` untuk satu judul dokumen, `block meta` untuk metadata tambahan, dan `block content` untuk konten utama. Gaya visual tetap berada di `static/css/style.css`.

## Tutorial form dan data delivery

Implementasi melanjutkan `ProjectForm` yang sudah mulai dibuat pada proyek ini dengan menambahkan model `Project`, migrasi `0005_project`, serta halaman Projects. `Achievement` dari Tugas 2 dan data prestasi sebelumnya tetap tersedia. Model Project menggunakan UUID serta field `title`, `description`, `tech_stack`, `project_url`, dan `project_image_url`; kedua URL opsional. Proyek baru tidak diisi dengan contoh fiktif dari tutorial. Masukkan judul, deskripsi, teknologi, dan tautan proyek milik sendiri melalui **Projects → Tambah Proyek**.

Form menampilkan error tanpa menghilangkan input. Setelah berhasil menyimpan, halaman Projects menampilkan pesan sukses. Pencarian judul memangkas spasi awal/akhir dan tidak membedakan kapitalisasi. Tombol **Hapus Proyek** membuka konfirmasi; Batal, tombol tutup, klik latar, atau Escape tidak menghapus data. Hanya tombol **Ya, Hapus** yang mengirim POST dengan token CSRF. Konfirmasi menggunakan Popover API pada browser modern.

Tutorial 05 mengganti alur serialisasi/deserialisasi di server: `show_projects` kini hanya merender kerangka halaman dan form. `static/js/projects.js` mengambil JSON melalui Fetch API, menampilkan loading/error/empty state, lalu merakit kartu dengan DOM dan `textContent`. Pencarian berjalan 300 ms setelah pengguna berhenti mengetik; Enter langsung mencari. `AbortController` membatalkan permintaan lama agar hasil pencarian terbaru tidak tertimpa. Tombol Reset dan Coba Lagi juga bekerja tanpa reload. Kartu geser diperbarui setiap data berubah.

Tombol **Tambah Proyek** membuka modal Popover API untuk superuser. Form dikirim ke `/projects/add-ajax/` dengan `FormData` serta token CSRF melalui header dan field form. Respons 201 menutup modal, menampilkan toast, dan memuat ulang daftar dengan filter yang masih aktif. Respons 400 menampilkan kesalahan validasi pada form dan toast; 403 menolak akun tanpa izin. Tombol simpan dinonaktifkan selama pengiriman. Endpoint form klasik, edit, hapus, dan star tetap tersedia; edit/hapus/star masih memakai navigasi atau POST biasa.

Untuk memeriksa data lewat browser atau Postman, buat proyek lewat form, kemudian gunakan GET:

```text
http://127.0.0.1:8000/api/projects/
http://127.0.0.1:8000/api/projects/?title=portfolio
http://127.0.0.1:8000/api/projects/xml/?title=portfolio
```

JSON berbentuk daftar objek dengan `model`, `pk`, dan `fields`. Field publik berisi `title`, `description`, `tech_stack`, `project_url`, dan `project_image_url`, ditambah `star_count` dan `is_starred` untuk pengguna saat ini; UUID proyek berada di `pk`. Relasi `starred_by`, ID pengguna pemberi star, username, email, dan data autentikasi tidak dikirim. XML tetap memakai serializer Django untuk lima field proyek tanpa metadata star. Database kosong menghasilkan `[]`; judul tanpa hasil tidak menyebabkan error. Kedua endpoint GET hanya membaca data.

Data JSON ditampilkan melalui `textContent`, termasuk judul, deskripsi, teknologi, dan pesan toast, sehingga payload HTML lama tetap menjadi teks. URL pada kartu dan halaman detail dibatasi ke HTTP/HTTPS, termasuk untuk data lama yang belum melewati validasi form. `ProjectForm` menghapus tag HTML pada ketiga field teks, menolak nilai wajib yang menjadi kosong, dan memvalidasi URL. Pembersihan input berlaku pada tambah klasik, tambah AJAX, dan edit; ini melengkapi perlindungan DOM, bukan menggantikannya. Komponen toast tersedia pada seluruh halaman melalui `showToast(title, message, type, duration)` dengan tipe `success`, `error`, atau `normal`.

URL gambar boleh memakai URL publik langsung. Jika memakai Google Drive, unggah gambar milik sendiri, atur **Anyone with the link → Viewer**, ambil ID berkas, kemudian isi field URL Gambar Proyek dengan `https://drive.google.com/thumbnail?id=FILE_ID&sz=w1000`. Form menyimpan URL, bukan mengunggah berkas. Akses dan keberhasilan pemuatan gambar eksternal bergantung pada penyedia gambar.

Konfigurasi `CSRF_TRUSTED_ORIGINS` sudah memakai `https://noe-andrew-myportofolio.pws.cs.ui.ac.id` tanpa slash penutup. Origin terdiri dari skema dan host, bukan path halaman; lihat [pengaturan CSRF Django](https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-trusted-origins). Token CSRF tetap diwajibkan pada semua form POST.

Tambah dan hapus proyek memerlukan superuser; edit memerlukan anggota grup `Editor` atau superuser. Pemeriksaan dilakukan pada server, termasuk ketika URL diakses langsung atau POST dikirim tanpa melalui tombol. Pengguna yang login tetapi tidak berhak memperoleh HTTP 403. Pengunjung yang belum login diarahkan ke login saat mengakses aksi klasik yang memerlukan akun; endpoint tambah AJAX membalas JSON 403 tanpa redirect. Semua POST juga harus lolos pemeriksaan CSRF. Tombol aksi hanya ditampilkan untuk peran yang sesuai.

Yang masih membutuhkan tindakan pemilik: isi proyek dan gambar pribadi, unggah/atur berbagi Google Drive bila digunakan, deploy perubahan ke PWS serta periksa Logs dan migrasi di sana, dan kumpulkan bukti/tugas pada platform kuliah bila diminta. Pengujian lokal tidak memverifikasi deployment atau pengumpulan.

## Tugas 4: autentikasi, Editor, dan star

Bagian portofolio yang dipilih untuk otorisasi adalah **Projects**. Daftar, pencarian, detail, JSON, dan XML dapat dibaca tanpa login. Registrasi membuat pengguna biasa; memilih peran tidak disediakan pada form publik.

| Peran | Baca daftar/detail | Beri/batalkan star | Tambah | Edit | Hapus |
| --- | --- | --- | --- | --- | --- |
| Pengunjung tanpa login | Ya | Login dahulu | Login dahulu | Login dahulu | Login dahulu |
| Pengguna biasa | Ya | Ya | 403 | 403 | 403 |
| Anggota grup `Editor` | Ya | Ya | 403 | Ya | 403 |
| Pemilik / superuser | Ya | Ya | Ya | Ya | Ya |

Untuk menyiapkan peran setelah mengambil perubahan Tugas 4:

1. Jalankan `python manage.py migrate`. Migrasi `0007_project_starred_by` membuat relasi star; migrasi `0008` menyiapkan grup `Editor`. Tidak ada akun nyata yang otomatis dinaikkan hak aksesnya.
2. Jika belum ada pemilik lokal, jalankan `python manage.py createsuperuser` dan isi kredensial melalui prompt.
3. Login sebagai pemilik di `/admin/`, buka **Authentication and Authorization → Users** (`/admin/auth/user/`), dan pilih akun yang memang akan menjadi editor. Akun dapat dibuat sebelumnya melalui `/register/`.
4. Pada bagian **Groups**, pindahkan **Editor** ke grup terpilih, lalu simpan. Tidak perlu mengaktifkan **Staff status** atau **Superuser status** untuk editor. Jika grup pernah dihapus, buat ulang dengan nama persis `Editor` melalui `/admin/auth/group/`.
5. Login menggunakan akun editor pada aplikasi, buka `/projects/`, dan gunakan **Edit Proyek** pada proyek yang tersedia. Tambah dan hapus tetap menjadi hak pemilik. Untuk mencabut hak editor, keluarkan akun dari grup tersebut di admin.

Implementasi memeriksa keanggotaan grup `Editor`; nama ini peka kapitalisasi. Editor mengubah konten melalui halaman aplikasi dan tidak memerlukan akses admin. Django menyediakan [grup untuk mengelompokkan pengguna dan hak akses](https://docs.djangoproject.com/en/5.2/topics/auth/default/#groups); pemilik menentukan sendiri akun yang dipercaya. Penetapan grup di lokal tidak mengubah database PWS sehingga perlu dilakukan terpisah setelah deployment bila editor juga diperlukan di sana.

`Project.starred_by` menggunakan `ManyToManyField` ke User. Satu pengguna mempunyai maksimal satu relasi star per proyek; POST berikutnya membatalkannya. Form star menyertakan `{% csrf_token %}`, sedangkan GET tidak mengubah star. Daftar dan detail menampilkan total star serta status pengguna yang sedang login tanpa menampilkan identitas pemberi star. Pengunjung memperoleh tautan login yang membawa kembali ke halaman asal. Parameter `next` dibatasi ke tujuan pada host aplikasi agar login tidak mengarahkan pengguna ke situs eksternal.

Checklist implementasi dan pemeriksaan manual empat peran tersedia di [checklist tugas](docs/task-checklist.md).

## Pengujian

```powershell
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py test --verbosity 2
```

Suite Django mencakup profil dan kontak, navigasi bersama, URL tidak ditemukan, model/status pengalaman, prestasi, serta Projects. Tes Projects mencakup validasi form, CRUD sesuai empat peran, daftar/detail publik, kontrol aksi, star/unstar, pencarian, format JSON/XML tanpa identitas pemberi star, kondisi kosong, escaping, pesan sukses, tujuan login, dan CSRF. Tes AJAX juga memeriksa status respons, sanitasi, metadata star per pengguna, serta efisiensi query. Tes menggunakan database pengujian tersendiri; pembersihan data seed dalam tes tidak menghapus data portofolio lokal. Jumlah tes terkini ditampilkan oleh runner.

Saat mengubah teks antarmuka, sesuaikan ekspektasi tes dengan perilaku yang dimaksud. Halaman profil menggunakan bahasa Inggris; form dan aksi Projects mengikuti bahasa Indonesia pada tutorial. Data seed perlu diisolasi agar tes pengalaman selesai tidak ikut membaca pengalaman lain yang masih berlangsung.

Untuk tutorial Selenium, instal dependency pengembangan dan jalankan suite browser terpisah:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements-dev.txt
.\env\Scripts\python.exe test_e2e.py --headless
```

Hapus `--headless` untuk melihat Chrome dikendalikan otomatis, atau tambahkan `--browser edge` / `--browser firefox`. Skrip menyiapkan server loopback dan database pengujian sementara; tidak perlu `runserver` manual, password baru, atau perubahan PWS. Password uji dibuat acak bila tidak disediakan. Selenium Manager memerlukan internet untuk mengunduh driver yang belum tersedia. `manage.py test` tetap dapat berjalan tanpa Selenium. Alur browser, konfigurasi password uji opsional, serta langkah intersepsi CSRF manual dijelaskan di [panduan Selenium dan Burp Suite](docs/browser-security-testing.md). Jalankan kedua suite setelah mengambil perubahan Tugas 4; hasil tes pada versi sebelumnya bukan verifikasi versi yang baru.

## Perkembangan mingguan

| Tahap | Implementasi |
| --- | --- |
| Tutorial 1 / Tugas 1 | Profil pribadi, tiga focus areas, CSS responsif, dan refleksi Tugas 1 |
| Tutorial 2 | Aplikasi `main`, model `Experience`, migrasi, context profil, routing, dan pengujian |
| Tugas 2 | Model `Achievement`, migrasi struktur dan data awal, halaman dinamis, admin, pengujian, dan template bersama |
| Tutorial form dan data delivery | Model/form `Project`, tambah/cari/hapus, JSON/XML, konfirmasi, pesan sukses, dan CSRF |
| Tutorial Selenium dan Burp Suite | Otomasi login, cookie, akses superuser, logout; tes CSRF dan panduan intersepsi request lokal |
| Tugas 4 | Grup Editor, otorisasi empat peran di server dan template, detail publik, star dengan CSRF, JSON/XML tanpa identitas pengguna, serta pengujian akses |
| Tutorial 05 | Daftar dan pencarian AJAX, debounce, modal tambah, toast global, perlindungan XSS/CSRF, serta pengujian browser |

Saat mengambil perubahan Tugas 2 dari Git, jalankan ulang instalasi dependency bila `requirements.txt` berubah, kemudian `migrate` dan `collectstatic --noinput` sebelum menyalakan server. Tidak perlu membuat migrasi baru hanya untuk menambahkan objek melalui admin.

Untuk Tugas 3, jalankan `migrate` sebelum mencoba form dan API Projects. Untuk Tutorial 04/Tugas 4, jalankan kembali `migrate`, tetapkan anggota grup `Editor` melalui admin sesuai panduan di atas, lalu jalankan pemeriksaan Django dan Selenium. Dependensi Selenium berada di `requirements-dev.txt` sehingga perlu diinstal terpisah pada lingkungan pengembangan.

Tutorial 05 tidak menambah migrasi atau dependency. Jika memakai hasil `collectstatic`, jalankan kembali `collectstatic --noinput` setelah mengambil aset JavaScript/CSS terbaru. Suite browser mencakup pembacaan dan pencarian AJAX, modal tambah, validasi, CSRF, toast, payload XSS lama, serta aksi star, detail, hapus, dan edit oleh Editor.

Audit ulang 29 September 2026 lulus **96 tes Django dan 7 skenario Selenium Chrome**. Regresi tambahan memeriksa respons pencarian yang terlambat, Enter tanpa pencarian ganda, kegagalan jaringan/HTML, serta filter aktif setelah menambah proyek. Respons tambah baru dianggap berhasil jika server mengirim HTTP 201 dengan UUID proyek valid; respons lain mempertahankan input. Rincian kesesuaian dan penyesuaian contoh ada di [checklist Tutorial 05](docs/task-checklist.md#audit-tutorial-05--29-september-2026).

### Tugas 1

1. Saya menggunakan elemen semantik HTML5 seperti `header`, `nav`, `main`, `section`, `article`, dan `footer`. Elemen tersebut membantu mengelompokkan isi halaman berdasarkan fungsi, sehingga struktur About Me lebih mudah dibaca, dirawat, dan dipahami oleh browser maupun pengguna yang menggunakan assistive technology. Elemen `section` digunakan untuk memisahkan bagian profil dan focus areas, sedangkan `article` digunakan untuk setiap item yang berdiri sendiri.

2. Tantangan responsive layout yang saya temukan adalah menjaga navbar, foto profil, teks bio, dan tiga item focus areas tetap terbaca pada layar kecil. Saya menggunakan CSS Grid untuk layout utama, kemudian mengubahnya menjadi satu kolom pada breakpoint mobile. Ukuran teks dan jarak navbar juga diperkecil agar menu tidak keluar dari layar atau bertabrakan.

3. Karena website masih static, informasi di dalamnya harus ditulis langsung pada template dan belum dapat dikelola melalui halaman admin atau database. Perubahan achievements, experience, dan focus areas juga masih memerlukan perubahan kode. Pada iterasi berikutnya, saya ingin menambahkan model database dan halaman admin agar konten portfolio dapat diperbarui secara dinamis, serta menambahkan formulir kontak yang dapat memproses pesan.

### Tugas 2

1. Ketika pengguna membuka `/achievements/`, Django membaca `portofolio/urls.py`. Baris `path("", include("main.urls"))` meneruskan pencocokan rute ke `main/urls.py`. Named route `main:show_achievements` memilih fungsi `show_achievements` pada `main/views.py`. View mempersiapkan QuerySet `Achievement.objects.all()` dan memasukkannya ke context dengan nama `achievement_list`. QuerySet dievaluasi ketika datanya diperlukan saat rendering. Django merender `templates/achievements.html`, yang mewarisi kerangka `base.html`. Perulangan `{% for achievement in achievement_list %}` menghasilkan kartu untuk setiap objek; `{% empty %}` menghasilkan pesan ketika tidak ada objek. Hasil HTML dikirim sebagai respons untuk ditampilkan browser. Dengan demikian, URL menentukan tujuan, model mengatur struktur dan akses data, view menyiapkan data, dan template mengatur tampilannya.

2. Data prestasi disimpan pada model supaya judul, deskripsi, penghargaan, gambar, dan urutannya dapat diperbarui melalui admin tanpa mengubah HTML. Satu pola kartu dapat menampilkan banyak objek, sehingga tidak perlu menyalin markup setiap menambah prestasi. Pemisahan ini mengurangi perbedaan struktur antarkartu dan memungkinkan data yang sama digunakan oleh halaman lain atau API pada pengembangan selanjutnya. Field model juga menyediakan tipe data dan aturan validasi yang dapat digunakan oleh form/admin. Template tetap boleh menyimpan teks antarmuka seperti judul halaman dan pesan kosong; yang berasal dari database adalah isi prestasinya. Pengambilan data dan kondisi tampilan dapat diuji terpisah dari perubahan desain CSS.

3. `makemigrations` membuat berkas instruksi perubahan struktur berdasarkan perbedaan model dan riwayat migrasi; perintah ini belum menerapkan perubahan tabel. `migrate` menjalankan instruksi migrasi yang belum diterapkan pada database yang aktif. Contohnya, penambahan model `Achievement` menghasilkan `0003_achievement.py`, kemudian `migrate` membuat tabelnya. Jika kelak ditambah field `organizer = models.CharField(max_length=255, blank=True)`, jalankan `makemigrations main`, tinjau berkas yang dihasilkan, commit berkas tersebut, lalu jalankan `migrate` pada lokal dan deployment. Migrasi data `0004_seed_achievements.py` secara terpisah memasukkan prestasi yang sebelumnya berada di HTML. Menambah satu prestasi lewat admin hanya mengubah isi tabel sehingga tidak memerlukan `makemigrations`.

## Deployment dan pengumpulan

URL proyek: <https://noe-andrew-myportofolio.pws.cs.ui.ac.id/>. Database PWS terpisah dari SQLite lokal. Atur environment produksi melalui tab Environs PWS sesuai konfigurasi proyek, termasuk `PRODUCTION=True`, `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, dan `SCHEMA`. Buat `SECRET_KEY` baru secara acak dan rahasia; jangan masukkan nilainya ke Git atau README.

Jika Experience, Achievements, dan Projects gagal dengan `invalid integer value "<5432>" for connection option "port"`, perbaiki `DB_PORT=5432` pada **Environs PWS**. Periksa juga nilai database lain agar memakai kredensial asli tanpa pembungkus contoh `<...>`. Lihat [panduan perbaikan database PWS](docs/pws-database.md) untuk langkah lengkap. Mengedit `.env.prod` lokal atau melakukan push Git saja tidak memperbarui Environs.

Konfigurasi produksi sekarang memvalidasi port serta pengaturan database saat aplikasi dimulai dan menggunakan `DEBUG=False`. Perbaiki Environs sebelum men-deploy perubahan ini; konfigurasi yang tidak valid akan menghentikan startup dengan pesan di Logs. SQLite lokal tetap digunakan ketika `PRODUCTION=False`.

Setelah perubahan diperiksa dan di-commit, perintah berikut mengirim commit aktif ke branch tujuan tanpa bergantung pada nama branch lokal:

```powershell
git push origin HEAD:main
git push pws HEAD:master
```

Pantau status dan Logs PWS hingga aplikasi berjalan; pastikan migrasi berhasil dan buka `/`, `/experience/`, `/achievements/`, `/projects/`, detail salah satu proyek, `/api/projects/`, serta `/static/css/style.css`. Periksa kembali hak empat peran pada deployment memakai akun milik sendiri. Keberhasilan lokal atau push GitHub tidak membuktikan deployment PWS sudah diperbarui. Proses deployment PWS pada tutorial menjalankan migrasi sebelum server siap.

Pengumpulan Tugas 2 menggunakan tautan **commit final yang sudah di-push**, bukan hanya tautan repositori. Ambil hash dengan `git rev-parse HEAD`, kemudian gunakan format `https://github.com/noeandrew-jm/myportofolio/commit/<hash>` dan buka tanpa login untuk memastikan akses publik. Deadline pada dokumen tugas adalah **14 September 2026, 23.59 WIB**. Tautan tersebut tetap harus dikumpulkan melalui slot SCELE yang benar. Pemilik proyek menyatakan Tutorial 2 sudah dikumpulkan; pernyataan ini bukan verifikasi otomatis terhadap SCELE.

Untuk **Individual Assignment 4**, tenggat pada instruksi yang dilampirkan adalah **Senin, 28 September 2026, pukul 23.59 WIB**; deadline **Tutorial 04** juga dipindahkan ke waktu yang sama. Siapkan commit akhir dengan pesan deskriptif mengikuti Conventional Commits, push sebelum tenggat, pastikan repositori GitHub publik, dan kirim tautan commit melalui slot SCELE yang sesuai. Commit yang di-push setelah tenggat tidak diterima menurut instruksi tugas. Pengerjaan melalui AI pada sesi Tugas 4 tidak melakukan commit, push, deployment, atau pengumpulan atas nama pemilik.

## Penggunaan AI

Proyek ini menggunakan bantuan **OpenAI Codex**. Pada sesi audit dan penyelesaian checklist, bantuan mencakup pemeriksaan instruksi tugas terhadap kode, implementasi model dan migrasi `Achievement`, pemindahan konten lama ke database, perbaikan HTML dan tautan, penyamaan template navbar/footer, penyesuaian serta penambahan tes, dan penyusunan dokumentasi ini.

Pada Tugas 4, Codex membantu membandingkan kode dengan lampiran tugas, membatasi edit untuk grup `Editor`/superuser, membuat detail proyek publik, membatasi field API agar relasi pengguna tidak bocor, memperbaiki interaksi star dan tujuan setelah login, serta menyesuaikan pengujian dan dokumentasi. Strategi prompting memakai instruksi tugas lengkap beserta konteks repositori, lalu memeriksa tiap persyaratan terhadap perilaku server, template, dan database. Perubahan dan hasil pemeriksaan dicatat di log; hasil yang belum dijalankan tidak dianggap lulus.

Pada 28 September 2026, GitHub Copilot membantu memindahkan label sesi login ke bawah tautan proyek, menambahkan glass Login/Register dan menu navigasi mobile, mengaudit checklist, menyelaraskan tes regresi dengan aturan akses/API yang berlaku, menambahkan tes star dan CSRF, serta mewajibkan `SECRET_KEY` dari environment produksi. Suite lokal dan Selenium dijalankan kembali setelah perubahan; detail hasil dan batas verifikasi dicatat di [log bantuan AI](docs/ai-log.md).

Strategi yang digunakan adalah memberi konteks dokumen tugas dan meminta audit terlebih dahulu, lalu meminta pengerjaan bagian yang bisa diselesaikan serta menanyakan informasi yang belum tersedia. URL LinkedIn diberikan langsung oleh pemilik proyek. Nama, foto, bio, serta isi pengalaman dan prestasi berasal dari data proyek yang sudah ada; AI tidak memverifikasi klaim prestasi atau membuat prestasi baru.

Keterbatasan AI terlihat pada kebutuhan memeriksa hasilnya: server yang mengembalikan HTTP 200 belum berarti seluruh checklist atau test lulus, migrasi seed dapat memengaruhi isolasi test, dan akses lokal berbeda dari deployment. Pengujian Django dan pemeriksaan browser digunakan untuk mengevaluasi perubahan. Jawaban refleksi Tugas 2 disusun dengan bantuan AI berdasarkan implementasi ini dan perlu dibaca serta dipahami oleh pemilik proyek sebelum dikumpulkan; tidak diklaim sebagai tulisan tanpa bantuan AI.

Audit Tugas 4 menemukan dua contoh keterbatasan implementasi sebelumnya: tombol yang disembunyikan tidak cukup jika endpoint edit masih publik, dan serialisasi seluruh field dapat memasukkan ID pemberi star setelah relasi baru ditambahkan. Karena itu, pemeriksaan akses harus mencakup request langsung serta isi JSON/XML. AI tidak mengetahui akun mana yang layak diberi hak editor dan tidak dapat menyimpulkan deployment atau pengumpulan berhasil dari tes lokal. Pemilik masih perlu menetapkan akun editor, memahami perubahan, serta menangani GitHub/PWS/SCELE. Tidak ada klaim bahwa pemilik sudah melakukan perbaikan manual atau meninjau seluruh hasil pada sesi ini.

Ringkasan prompt dan keputusan yang benar-benar tersedia pada sesi ini ada di [log bantuan AI](docs/ai-log.md). Riwayat bantuan sebelum sesi ini tidak direkonstruksi atau dibuat-buat.

## Referensi

- [Tutorial 1 PBP — deployment PWS](https://pbp.cs.ui.ac.id/tutorial/tutorial-1.html#pembuatan-akun-dan-deployment-melalui-pws-pacil-web-service)
- [Migrasi Django 5.2](https://docs.djangoproject.com/en/5.2/topics/migrations/)
- [Menulis dan menjalankan tes Django 5.2](https://docs.djangoproject.com/en/5.2/topics/testing/overview/)
