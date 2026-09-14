# Portofolio Noe Andrew

Website portofolio pribadi untuk Proyek Individu PBP, dibangun bertahap menggunakan Django 5.2, HTML5, dan CSS3. Profil dan tiga focus areas ada di halaman utama; pengalaman dan prestasi ditampilkan dari database pada halaman terpisah.

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
| `/admin/` | Pengelolaan pengalaman dan prestasi | Django admin; perlu login |

`migrate` membuat tabel dan memasukkan dua pengalaman serta dua prestasi awal dari konten portofolio yang sudah ada. Migrasi data hanya dijalankan sekali; perubahan selanjutnya bisa dilakukan melalui admin. Database lokal tidak disertakan di Git.

Untuk membuat akun admin milik sendiri:

```powershell
.\env\Scripts\python.exe manage.py createsuperuser
```

Model `Achievement` memiliki UUID sebagai primary key, serta `title`, `description`, `award`, `thumbnail`, dan `display_order`. `thumbnail` memakai `CharField` karena menyimpan alamat gambar, termasuk path lokal seperti `/static/image/PKM.jpeg`; field ini bukan upload berkas. `award` dan `thumbnail` boleh kosong. Urutan tampilan mengikuti `display_order`, lalu judul dan ID.

`templates/base.html` memuat kerangka HTML, CSS, navbar, dan footer bersama. Isi tiap halaman ada di `index.html`, `experience.html`, dan `achievements.html`. Gaya visual tetap berada di `static/css/style.css`.

## Pengujian

```powershell
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py test --verbosity 2
```

Suite berisi 14 tes: profil dan kontak, navigasi bersama, URL tidak ditemukan, model dan status pengalaman, kondisi kosong, serta halaman prestasi. Tes prestasi mencakup URL/template, beberapa objek dari database, kondisi kosong, field opsional, pembaruan data, dan HTML escaping. Tes menggunakan database pengujian tersendiri; pembersihan data seed dalam tes tidak menghapus data portofolio lokal.

Saat mengubah teks antarmuka, sesuaikan ekspektasi tes dengan perilaku yang dimaksud. Antarmuka halaman ini berbahasa Inggris. Data seed perlu diisolasi agar tes pengalaman selesai tidak ikut membaca pengalaman lain yang masih berlangsung.

## Perkembangan mingguan

| Tahap | Implementasi |
| --- | --- |
| Tutorial 1 / Tugas 1 | Profil pribadi, tiga focus areas, CSS responsif, dan refleksi Tugas 1 |
| Tutorial 2 | Aplikasi `main`, model `Experience`, migrasi, context profil, routing, dan pengujian |
| Tugas 2 | Model `Achievement`, migrasi struktur dan data awal, halaman dinamis, admin, pengujian, dan template bersama |

Saat mengambil perubahan Tugas 2 dari Git, jalankan ulang instalasi dependency bila `requirements.txt` berubah, kemudian `migrate` dan `collectstatic --noinput` sebelum menyalakan server. Tidak perlu membuat migrasi baru hanya untuk menambahkan objek melalui admin.

### Tugas 1

1. Saya menggunakan elemen semantik HTML5 seperti `header`, `nav`, `main`, `section`, `article`, dan `footer`. Elemen tersebut membantu mengelompokkan isi halaman berdasarkan fungsi, sehingga struktur About Me lebih mudah dibaca, dirawat, dan dipahami oleh browser maupun pengguna yang menggunakan assistive technology. Elemen `section` digunakan untuk memisahkan bagian profil dan focus areas, sedangkan `article` digunakan untuk setiap item yang berdiri sendiri.

2. Tantangan responsive layout yang saya temukan adalah menjaga navbar, foto profil, teks bio, dan tiga item focus areas tetap terbaca pada layar kecil. Saya menggunakan CSS Grid untuk layout utama, kemudian mengubahnya menjadi satu kolom pada breakpoint mobile. Ukuran teks dan jarak navbar juga diperkecil agar menu tidak keluar dari layar atau bertabrakan.

3. Karena website masih static, informasi di dalamnya harus ditulis langsung pada template dan belum dapat dikelola melalui halaman admin atau database. Perubahan achievements, experience, dan focus areas juga masih memerlukan perubahan kode. Pada iterasi berikutnya, saya ingin menambahkan model database dan halaman admin agar konten portfolio dapat diperbarui secara dinamis, serta menambahkan formulir kontak yang dapat memproses pesan.

### Tugas 2

1. Ketika pengguna membuka `/achievements/`, Django membaca `portofolio/urls.py`. Baris `path("", include("main.urls"))` meneruskan pencocokan rute ke `main/urls.py`. Named route `main:show_achievements` memilih fungsi `show_achievements` pada `main/views.py`. View mempersiapkan QuerySet `Achievement.objects.all()` dan memasukkannya ke context dengan nama `achievement_list`. QuerySet dievaluasi ketika datanya diperlukan saat rendering. Django merender `templates/achievements.html`, yang mewarisi kerangka `base.html`. Perulangan `{% for achievement in achievement_list %}` menghasilkan kartu untuk setiap objek; `{% empty %}` menghasilkan pesan ketika tidak ada objek. Hasil HTML dikirim sebagai respons untuk ditampilkan browser. Dengan demikian, URL menentukan tujuan, model mengatur struktur dan akses data, view menyiapkan data, dan template mengatur tampilannya.

2. Data prestasi disimpan pada model supaya judul, deskripsi, penghargaan, gambar, dan urutannya dapat diperbarui melalui admin tanpa mengubah HTML. Satu pola kartu dapat menampilkan banyak objek, sehingga tidak perlu menyalin markup setiap menambah prestasi. Pemisahan ini mengurangi perbedaan struktur antarkartu dan memungkinkan data yang sama digunakan oleh halaman lain atau API pada pengembangan selanjutnya. Field model juga menyediakan tipe data dan aturan validasi yang dapat digunakan oleh form/admin. Template tetap boleh menyimpan teks antarmuka seperti judul halaman dan pesan kosong; yang berasal dari database adalah isi prestasinya. Pengambilan data dan kondisi tampilan dapat diuji terpisah dari perubahan desain CSS.

3. `makemigrations` membuat berkas instruksi perubahan struktur berdasarkan perbedaan model dan riwayat migrasi; perintah ini belum menerapkan perubahan tabel. `migrate` menjalankan instruksi migrasi yang belum diterapkan pada database yang aktif. Contohnya, penambahan model `Achievement` menghasilkan `0003_achievement.py`, kemudian `migrate` membuat tabelnya. Jika kelak ditambah field `organizer = models.CharField(max_length=255, blank=True)`, jalankan `makemigrations main`, tinjau berkas yang dihasilkan, commit berkas tersebut, lalu jalankan `migrate` pada lokal dan deployment. Migrasi data `0004_seed_achievements.py` secara terpisah memasukkan prestasi yang sebelumnya berada di HTML. Menambah satu prestasi lewat admin hanya mengubah isi tabel sehingga tidak memerlukan `makemigrations`.

## Deployment dan pengumpulan

URL proyek: <https://noe-andrew-myportofolio.pws.cs.ui.ac.id/>. Database PWS terpisah dari SQLite lokal. Atur environment produksi melalui tab Environs PWS sesuai konfigurasi proyek, termasuk `PRODUCTION=True`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, dan `SCHEMA`. Jangan masukkan nilai kredensial ke Git atau README.

Setelah perubahan diperiksa dan di-commit, perintah berikut mengirim commit aktif ke branch tujuan tanpa bergantung pada nama branch lokal:

```powershell
git push origin HEAD:main
git push pws HEAD:master
```

Pantau status dan Logs PWS hingga aplikasi berjalan; pastikan migrasi berhasil dan buka `/`, `/experience/`, `/achievements/`, serta `/static/css/style.css`. Keberhasilan lokal atau push GitHub tidak membuktikan deployment PWS sudah diperbarui. Proses deployment PWS pada tutorial menjalankan migrasi sebelum server siap.

Pengumpulan Tugas 2 menggunakan tautan **commit final yang sudah di-push**, bukan hanya tautan repositori. Ambil hash dengan `git rev-parse HEAD`, kemudian gunakan format `https://github.com/noeandrew-jm/myportofolio/commit/<hash>` dan buka tanpa login untuk memastikan akses publik. Deadline pada dokumen tugas adalah **14 September 2026, 23.59 WIB**. Tautan tersebut tetap harus dikumpulkan melalui slot SCELE yang benar. Pemilik proyek menyatakan Tutorial 2 sudah dikumpulkan; pernyataan ini bukan verifikasi otomatis terhadap SCELE.

## Penggunaan AI

Proyek ini menggunakan bantuan **OpenAI Codex**. Pada sesi audit dan penyelesaian checklist, bantuan mencakup pemeriksaan instruksi tugas terhadap kode, implementasi model dan migrasi `Achievement`, pemindahan konten lama ke database, perbaikan HTML dan tautan, penyamaan template navbar/footer, penyesuaian serta penambahan tes, dan penyusunan dokumentasi ini.

Strategi yang digunakan adalah memberi konteks dokumen tugas dan meminta audit terlebih dahulu, lalu meminta pengerjaan bagian yang bisa diselesaikan serta menanyakan informasi yang belum tersedia. URL LinkedIn diberikan langsung oleh pemilik proyek. Nama, foto, bio, serta isi pengalaman dan prestasi berasal dari data proyek yang sudah ada; AI tidak memverifikasi klaim prestasi atau membuat prestasi baru.

Keterbatasan AI terlihat pada kebutuhan memeriksa hasilnya: server yang mengembalikan HTTP 200 belum berarti seluruh checklist atau test lulus, migrasi seed dapat memengaruhi isolasi test, dan akses lokal berbeda dari deployment. Pengujian Django dan pemeriksaan browser digunakan untuk mengevaluasi perubahan. Jawaban refleksi Tugas 2 disusun dengan bantuan AI berdasarkan implementasi ini dan perlu dibaca serta dipahami oleh pemilik proyek sebelum dikumpulkan; tidak diklaim sebagai tulisan tanpa bantuan AI.

Ringkasan prompt dan keputusan yang benar-benar tersedia pada sesi ini ada di [log bantuan AI](docs/ai-log.md). Riwayat bantuan sebelum sesi ini tidak direkonstruksi atau dibuat-buat.

## Referensi

- [Tutorial 1 PBP — deployment PWS](https://pbp.cs.ui.ac.id/tutorial/tutorial-1.html#pembuatan-akun-dan-deployment-melalui-pws-pacil-web-service)
- [Migrasi Django 5.2](https://docs.djangoproject.com/en/5.2/topics/migrations/)
- [Menulis dan menjalankan tes Django 5.2](https://docs.djangoproject.com/en/5.2/topics/testing/overview/)
