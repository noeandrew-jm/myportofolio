# Log bantuan AI — 14 September 2026

Log ini merangkum percakapan yang tersedia untuk audit dan penyelesaian checklist portofolio. Ini bukan ekspor lengkap seluruh percakapan atau rekonstruksi sesi sebelumnya.

## Prompt pemilik proyek

1. "sebelum aku lanjut mengerjakan design web saya, pastikan seluruh checklist sudah terpenuhi"
   - Konteks: dokumen Tugas 1, Tugas 2, dan Tutorial 2 diberikan sebagai lampiran.
   - Hasil audit: model baru untuk Tugas 2 belum ada, Achievements masih hard-coded, tiga test gagal, README belum memuat Tugas 2, HTML profil tidak seimbang, dan dua halaman PWS mengembalikan 404.
2. "apakah semua yang belum selesai itu bisa kamu kerjakan semua? bilamana ada yang tidak karena kurang informasi dari saya beritahu, tapi kerjakan dulu yang bisa kamu kerjakan"
   - Keputusan: menggunakan bagian Achievements yang sudah ada sebagai fitur database baru; mempertahankan konten pribadi dan arah desain.
3. Klarifikasi URL LinkedIn: "www.linkedin.com/in/noeandrew".
   - URL dipasang sebagai `https://www.linkedin.com/in/noeandrew`.
4. Klarifikasi status Tutorial 2 di SCELE: "Sudah dikumpulkan".
   - Informasi berasal dari pemilik proyek, tidak diverifikasi melalui akses akun SCELE.

## Bagian yang dibantu Codex

- Model `Achievement`, migrasi struktur dan migrasi data untuk dua prestasi yang sebelumnya tertulis pada template.
- QuerySet pada view dan template dengan perulangan serta pesan kosong.
- Registrasi Achievement pada admin, termasuk pengaturan urutan tampilan.
- Template bersama, perbaikan pasangan tag HTML, tautan kontak, dan CSS untuk layar sempit.
- Penyelarasan bahasa test dengan UI Inggris dan isolasi data seed pada database test.
- Test perilaku Achievement, navigasi, dan profil; dokumentasi setup dan jawaban refleksi Tugas 2.

## Evaluasi hasil dan batasannya

Hasil pemeriksaan lokal setelah implementasi:

- `manage.py check`: tidak ada masalah konfigurasi.
- `manage.py makemigrations --check --dry-run`: tidak ada perubahan model yang belum memiliki migrasi.
- `manage.py test`: 14 test lulus.
- `manage.py showmigrations main`: migrasi `0001` sampai `0004` sudah diterapkan.
- Pemeriksaan browser Edge pada `/`, `/experience/`, dan `/achievements/` di lebar 320, 390, 768, dan 1440 px: seluruh gambar termuat, navigasi aktif sesuai halaman, dan tidak ada overflow horizontal. Judul Achievements juga diperiksa ulang pada 320 px setelah ukuran minimumnya disesuaikan.

Tes tidak hanya memeriksa respons HTTP: tes juga menambahkan beberapa objek, mengubah data, menghapus objek pada database test untuk memeriksa pesan kosong, serta memastikan teks HTML dari data di-escape. Kasus ini membedakan halaman database dari template hard-coded yang sekadar dapat dibuka.

Kebenaran informasi pribadi, pemahaman jawaban refleksi, dan pengumpulan tugas tetap memerlukan keterlibatan pemilik proyek. Log ini tidak mengklaim bahwa pemilik sudah meninjau seluruh kode atau bahwa AI dapat menjamin nilai. Hasil pengecekan kode tidak menggantikan bukti pengumpulan di SCELE.

## Implementasi tutorial form dan data delivery — 16 September 2026

Pemilik meminta seluruh tutorial skeleton, form, dan data delivery diterapkan ke kode, serta meminta diberi tahu untuk bagian di luar akses workspace, seperti PWS, data pribadi, dan Google Drive. Kode awal sudah memiliki form Projects parsial, tetapi model Project dan beberapa import/rute belum tersedia.

Implementasi melanjutkan Projects yang sudah mulai dibuat. Pertanyaan pilihan Projects/Achievements disampaikan karena tutorial menyebut penyesuaian terhadap objek Tugas 2; belum ada jawaban saat implementasi ini dicatat, sehingga pekerjaan dilanjutkan dengan asumsi Projects yang sudah dinyatakan kepada pemilik. Prestasi Achievement yang ada tidak dipindahkan atau dihapus.

Bantuan mencakup penyelesaian template bersama, model/migrasi/admin Project, ModelForm, tambah dan hapus dengan CSRF, pencarian judul, API JSON serta percobaan XML, deserialisasi JSON ke halaman, konfirmasi hapus, pesan sukses, CSS responsif, serta dokumentasi penggunaan. Tautan dan nama contoh disesuaikan dengan informasi Noe Andrew yang sudah ada. Tidak ada isi proyek pribadi atau prestasi baru yang dibuat oleh AI.

Verifikasi lokal:

- `manage.py check`: tidak ada masalah.
- `manage.py makemigrations --check --dry-run`: tidak ada perubahan model tanpa migrasi.
- `manage.py test`: 43 tes lulus, termasuk 28 tes Projects baru.
- Migrasi `0005_project` diterapkan pada SQLite lokal; dua Experience dan dua Achievement yang ada tetap tersimpan.
- `collectstatic --noinput` memperbarui aset lokal.
- Tujuh halaman/endpoint utama mengembalikan HTTP 200 pada database lokal.
- Browser Edge headless dengan database terisolasi: 77 pemeriksaan lulus pada lebar 320, 390, 768, dan 1440 px, mencakup layout, form, pencarian, API, pembatalan konfirmasi, serta hapus dengan pesan sukses. Pemeriksaan visual menemukan teks tombol Cari membungkus; CSS diperbaiki agar teks tombol tetap satu baris.
- Setelah perbaikan CSS, 17 pemeriksaan khusus pencarian dan layout kembali lulus pada keempat lebar layar. Tidak ditemukan error JavaScript; permintaan favicon yang belum tersedia mengembalikan 404. Server dan browser pengujian telah dihentikan.

Deployment PWS, isi proyek pribadi, akses gambar Google Drive, dan pengumpulan tugas belum dilakukan atau diverifikasi. Form publik mengikuti tahap tutorial tanpa autentikasi pemilik; tip kode rahasia pada akhir tutorial merupakan langkah opsional yang belum diaktifkan.

## Tutorial Selenium dan Burp Suite — 27 September 2026

Pemilik memberikan lampiran tutorial otomasi browser dan intersepsi CSRF, lalu meminta: "tambahkan hal ini. bilamana butuh bantuan saya seperti eksternal, pws, dll beritahu. namun bila tidak ada tambahkan tanpa ada kesalahan".

Bantuan Codex mencakup runner Selenium `test_e2e.py`, dependency pengembangan terpisah, pemeriksaan login/cookie/otorisasi/logout dan CSRF, serta [panduan menjalankan tes dan demonstrasi Burp](browser-security-testing.md). Dokumentasi Selenium, PortSwigger, dan Django digunakan untuk memeriksa petunjuk driver, proxy, serta validasi token.

Skrip tutorial disesuaikan agar server loopback dan database SQLite pengujiannya dibuat otomatis. Akun `burhan_test` dan `admin_test` hanya hidup di database sementara tersebut. Password dapat dibaca dari environment atau dibuat acak dalam memori. Pendekatan ini menghindari perubahan akun pada database portofolio maupun PWS dan tidak memerlukan kredensial baru dari pemilik.

README diselaraskan dengan otorisasi yang sudah tersedia: tambah dan hapus proyek memerlukan superuser, sedangkan endpoint edit masih publik. Pernyataan form publik pada catatan 16 September menggambarkan keadaan saat itu, bukan perilaku terkini.

Verifikasi lokal pada sesi ini:

- `manage.py check`: tidak ada masalah.
- `manage.py makemigrations --check --dry-run`: tidak ada perubahan model tanpa migrasi.
- `manage.py test --noinput`: seluruh 70 tes Django lulus, termasuk 12 tes autentikasi, otorisasi, star, dan CSRF baru.
- `test_e2e.py --headless`: seluruh alur lulus pada Chrome 153 dengan Selenium 4.49.0, termasuk POST tanpa token ditolak tanpa menyimpan data, POST bertoken sah berhasil, dan cookie dibersihkan saat logout.
- Selenium menggulir tombol submit ke tengah layar sebelum klik agar animasi smooth scroll tidak menyebabkan klik di luar viewport. Browser, server uji, dan database sementara dibersihkan saat selesai.

Interaksi pada antarmuka Burp dan screenshot untuk tugas memerlukan tindakan pemilik jika diminta oleh pengajar. Demonstrasi Burp belum dijalankan. Tutorial lokal ini tidak memerlukan deployment PWS, dan tidak membuktikan deployment atau pengumpulan tugas sudah dilakukan.

## Audit dan penyelesaian checklist Tugas 4 — 28 September 2026

Prompt pemilik proyek: "kerjakan dan pastikan keseluruhan checklist sudah terisi dan benar dan nilai 4/4". Sebelumnya pemilik meminta sesi terakhir login ditempatkan di bawah tautan proyek, desain NPM/Program dipertahankan, tombol Login/Register mendapat liquid glass, dan navbar mobile diganti menu tiga titik.

GitHub Copilot mengaudit view, model, migration, template, API, dokumentasi, dan tes terhadap checklist. Bantuan mencakup penempatan sesi profil, glass Login/Register, disclosure navbar mobile, penyelarasan tes lama agar mengikuti matriks authorization dan allowlist API yang sebenarnya, tes star yang memverifikasi login, POST-only, CSRF, count, dan status, serta penggantian secret tetap dengan secret lokal sementara dan `SECRET_KEY` wajib dari environment produksi. README dan log ini diperbarui untuk mencatat bantuan AI dan batas verifikasinya.

Verifikasi lokal setelah perubahan:

- `manage.py test --verbosity 2`: seluruh 79 tes lulus.
- `test_e2e.py --headless`: alur login, role, CSRF, operasi superuser, dan logout lulus pada database sementara.
- `manage.py check`: tidak ada masalah.
- `manage.py makemigrations --check --dry-run`: tidak ada perubahan model tanpa migration.
- Migration `0008_create_editor_group` diterapkan pada SQLite lokal dan grup `Editor` terverifikasi ada. Database PWS tidak diakses atau diubah.
- Pemeriksaan browser mobile 390 px sebelumnya mengonfirmasi menu terbuka tanpa overflow, sesi di bawah tautan proyek, dan dua tombol auth memiliki layer liquid glass.

PWS harus diberi `SECRET_KEY` acak baru melalui Environs sebelum menjalankan versi ini; nilai rahasia lama yang pernah dipakai harus dirotasi. Migration juga perlu diterapkan terpisah di PWS. Worktree lokal masih harus ditinjau, di-commit, dan di-push oleh pemilik; GitHub, deployment, status publik repositori, dan pengumpulan SCELE tidak diverifikasi. Nilai tugas tetap ditentukan penilai, bukan dijamin oleh AI.

## Tutorial 05 — 29 September 2026

Pemilik melampirkan Tutorial 05: Web Interactivity with JavaScript dan meminta implementasi serta penyelesaiannya. Codex menyesuaikan tutorial dengan portofolio yang sudah ada: toast global, daftar proyek melalui Fetch API, pencarian dengan debounce 300 ms dan pembatalan permintaan lama, modal tambah proyek, endpoint POST AJAX dengan validasi/otorisasi/CSRF, serta sanitasi input dan rendering DOM yang aman dari XSS.

Tampilan kartu geser, detail, edit oleh Editor, star, dan konfirmasi hapus dipertahankan. JSON menambahkan jumlah dan status star tanpa identitas pemberi star, mengikuti batas data publik proyek sebelumnya. Input dan tombol simpan dikunci selama POST untuk mencegah pengiriman ganda serta hilangnya draft baru. Toast ditempatkan di dalam dialog yang terbuka agar klik notifikasi tidak menutup modal melalui light dismissal; perilaku popover diperiksa pada [dokumentasi MDN](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API/Using#nested_popovers).

Pengujian memakai database sementara dan server loopback. Sebanyak 94 tes Django dan 5 alur Selenium Chrome lulus, termasuk AJAX, debounce, loading/error/empty, validasi, CSRF, XSS, Editor, star/detail/hapus, layout mobile 390 px, fokus keyboard, serta proxy aksi kartu geser. Pemeriksaan sistem dan migrasi tidak menemukan masalah; JavaScript lulus pemeriksaan sintaks. Screenshot mobile dan desktop diperiksa. Tidak ada perubahan skema atau dependency baru. Perubahan belum di-commit, di-push, di-deploy ke PWS, atau dikumpulkan ke SCELE.

Audit ulang pada tanggal yang sama mengikuti permintaan pemilik: "selain commit dan pws. check apakah program saya sudah memenuhi keselurhan ini. bilamana belum kerjakan dengan sempurna". Codex memeriksa kembali lampiran terhadap implementasi dan mempertahankan perubahan yang sudah ada. Perbaikan mencakup `.venv/` pada `.gitignore`, penyaringan URL legacy pada halaman detail, serta pemeriksaan HTTP 201 dan UUID respons tambah agar halaman HTML HTTP 200 tidak disalahartikan sebagai keberhasilan. Dokumentasi frontend dan checklist diselaraskan dengan perilaku AJAX.

Hasil audit ulang: 96 tes Django dan 7 skenario Selenium Chrome lulus. Skenario tambahan mencakup query awal URL, Enter tanpa debounce ganda, respons lama yang selesai setelah pencarian terbaru, kegagalan jaringan/HTML, draft yang dipertahankan, dan filter aktif setelah berhasil menambah proyek. Pemeriksaan konfigurasi, migrasi, sintaks JavaScript, dan whitespace diff lulus; screenshot modal desktop dan mobile diperiksa. Chrome sempat crash sebelum membuka aplikasi ketika dijalankan dalam sandbox; suite berhasil setelah dijalankan dengan izin di luar sandbox, tetap memakai server loopback dan database sementara. Tidak ada commit, push, perubahan data portofolio, deployment PWS, atau pengumpulan SCELE pada audit ulang ini.
