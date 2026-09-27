# Tutorial Selenium dan Burp Suite

Tutorial ini menguji alur login, cookie, otorisasi superuser, dan validasi CSRF pada aplikasi portofolio. Skrip Selenium ada di [`test_e2e.py`](../test_e2e.py); Burp Suite digunakan untuk melihat dan mengubah request secara manual. Tidak perlu mengubah Environs atau database PWS untuk menjalankan tutorial ini.

## 1. Pengujian otomatis dengan Selenium

Jalankan dari folder yang berisi `manage.py` menggunakan PowerShell:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements-dev.txt
.\env\Scripts\python.exe test_e2e.py
```

Perintah kedua membuka Chrome dan mengendalikan browser secara otomatis. Untuk menjalankan tanpa jendela browser:

```powershell
.\env\Scripts\python.exe test_e2e.py --headless
```

Pilihan browser lain:

```powershell
.\env\Scripts\python.exe test_e2e.py --browser edge --headless
.\env\Scripts\python.exe test_e2e.py --browser firefox --headless
```

Gunakan browser yang tersedia di komputer. Selenium Manager mencari driver yang sesuai dengan versi browser, mengunduhnya bila diperlukan, lalu menyimpannya dalam cache. Siapkan koneksi internet untuk instalasi dependency dan pengunduhan driver pertama; pembaruan browser juga dapat memerlukan driver baru. Lihat [dokumentasi resmi Selenium Manager](https://www.selenium.dev/documentation/selenium_manager/).

**Tidak perlu menjalankan `manage.py runserver` untuk skrip ini.** Runner menyalakan server Django sendiri pada `127.0.0.1` dengan port yang tersedia, menyiapkan database SQLite pengujian sementara, lalu membersihkan database dan menghentikan server saat pengujian selesai. Akun `burhan_test` dan `admin_test` hanya dibuat di database pengujian. Akun dan konten pada `db.sqlite3` serta database PWS tidak diubah.

Selenium hanya menjadi dependency pengembangan di `requirements-dev.txt`. Deployment tetap menggunakan `requirements.txt`. Suite browser dijalankan melalui `test_e2e.py`, terpisah dari `manage.py test`, sehingga tes Django biasa tidak memerlukan browser atau Selenium.

### Password opsional

Skrip dapat langsung dijalankan tanpa mengisi password. Jika tidak disediakan, password akun uji dibuat acak dalam memori. Untuk memakai password uji sendiri, tambahkan variabel berikut ke `.env` di sebelah `manage.py` dan isi nilainya sendiri:

| Variabel | Digunakan untuk |
| --- | --- |
| `E2E_USER_PASSWORD` | Password akun biasa `burhan_test` |
| `E2E_ADMIN_PASSWORD` | Password akun superuser `admin_test` |

Environment variable terminal juga dapat digunakan. Password tidak ditulis ke kode atau dicetak pada output tes. `.env` sudah diabaikan oleh Git. Pengaturan ini hanya berlaku untuk akun dalam database pengujian sementara; akun tersebut tidak tersedia untuk login manual setelah skrip selesai.

### Lima alur yang diperiksa

| Tahap | Hasil yang diperiksa |
| --- | --- |
| CSRF form login | Input `csrfmiddlewaretoken` berisi nilai dan cookie `csrftoken` tersedia. |
| Login pengguna biasa | Redirect ke halaman utama, nama `burhan_test` terlihat, cookie `sessionid` dan `last_login` tersedia, serta label sesi terakhir login tampil. |
| Otorisasi pengguna biasa | Akses `/projects/add/` ditolak sebagai Forbidden. |
| Login superuser | Akun `admin_test` terlihat pada navigasi dan form tambah proyek dapat dibuka. |
| Logout | Navigasi kembali menawarkan login dan cookie sesi serta `last_login` dibersihkan. |

Sesudah superuser membuka form, suite juga menghapus input token CSRF sebelum submit dan memastikan proyek tidak tersimpan. Sebagai pembanding, submit dengan token yang sah harus berhasil dan proyek tampil. Setelah logout, akses form kembali harus mengarah ke login. Semua proyek uji tetap berada di database sementara.

Periksa output terminal: setiap tahap yang berhasil menghasilkan `[PASS]`; kegagalan membuat proses berakhir dengan kode keluar bukan nol. Jangan menyimpulkan berhasil hanya karena browser sempat terbuka.

Tes Django memeriksa status HTTP dan perubahan database secara langsung, termasuk penolakan POST tanpa token CSRF yang sah. Jalankan pemeriksaan aplikasi berikut secara terpisah:

```powershell
$env:PRODUCTION = 'False'
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py test --verbosity 2
```

## 2. Demonstrasi CSRF menggunakan Burp Suite

Bagian ini memerlukan interaksi pada aplikasi desktop Burp Suite. Jika tugas meminta screenshot Burp, lakukan langkah ini dan ambil bukti dari hasil yang benar-benar tampil. Tes otomatis tidak menghasilkan bukti intersepsi pada antarmuka Burp.

Pasang [Burp Suite Community Edition dari PortSwigger](https://portswigger.net/burp/communitydownload), lalu jalankan aplikasi. Gunakan browser bawaannya melalui **Proxy > Intercept > Open browser**; browser ini sudah dikonfigurasi untuk menggunakan proxy Burp. Posisi tombol dapat sedikit berbeda menurut versi. Lihat [panduan intersepsi resmi](https://portswigger.net/burp/documentation/desktop/getting-started/intercepting-http-traffic).

### Siapkan server dan akun lokal

Pastikan `.env` untuk server lokal memakai `PRODUCTION=False`. Tetapkan juga pada terminal karena nilai environment terminal mengalahkan `.env`, kemudian jalankan:

```powershell
$env:PRODUCTION = 'False'
.\env\Scripts\python.exe manage.py migrate
.\env\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Gunakan akun superuser lokal milik sendiri. Jika belum mempunyai akun tersebut, jalankan perintah berikut di terminal lain dan isi kredensial melalui prompt:

```powershell
$env:PRODUCTION = 'False'
.\env\Scripts\python.exe manage.py createsuperuser
```

Server ini menggunakan database lokal biasa. Akun sementara dari Selenium tidak tersedia di sini. Gunakan judul proyek uji yang mudah dikenali untuk membedakannya dari portofolio asli.

### Intersepsi dan ubah token

1. Atur **Intercept off** agar navigasi dan login berjalan lancar. Di browser Burp, buka `http://127.0.0.1:8000/login/`, lalu masuk dengan superuser lokal.
2. Buka `http://127.0.0.1:8000/projects/add/`. Isi field wajib dengan data uji; biarkan field URL opsional kosong bila tidak dibutuhkan. Jangan submit dulu.
3. Atur **Intercept on** dan klik **Tambah Proyek** pada form. Pilih request **POST `/projects/add/`** yang tertahan, bukan request aset. Cookie `sessionid`, `last_login`, dan `csrftoken` serta body form dapat diperiksa di request ini.
4. Pada body request, kosongkan nilai parameter `csrfmiddlewaretoken` sehingga menjadi `csrfmiddlewaretoken=`. Biarkan cookie sesi dan field proyek tetap sama. Jika ada header `X-CSRFToken`, hapus juga agar tidak ada token alternatif. Form proyek biasa tidak mengirim header tersebut.
5. Klik **Forward**, lalu atur **Intercept off** agar respons dan request berikutnya dapat berjalan. Pengubahan request yang tertahan merupakan fungsi standar [Burp Proxy](https://portswigger.net/burp/documentation/desktop/getting-started/modifying-http-requests).
6. Periksa respons di **Proxy > HTTP history**: status harus **403 Forbidden**, dengan keterangan kegagalan verifikasi CSRF pada halaman. Terminal Django juga dapat menampilkan alasan penolakan CSRF. Buka Projects dan pastikan proyek uji tadi tidak tersimpan.
7. Sebagai pembanding, buka ulang form untuk memperoleh token baru, isi data uji, dan submit dengan **Intercept off**. Penyimpanan yang berhasil menampilkan pesan sukses dan proyek baru di daftar. Hapus proyek uji melalui konfirmasi hapus setelah selesai.

`CsrfViewMiddleware` memvalidasi token sebelum view menyimpan data. Cookie sesi yang valid tidak menggantikan token CSRF. Sebaliknya, token CSRF yang valid tidak memberikan hak superuser: otorisasi tetap diperiksa di view. Django mengembalikan 403 untuk request dengan token yang tidak sah; lihat [cara kerja CSRF Django](https://docs.djangoproject.com/en/5.2/ref/csrf/).

Jika tugas meminta bukti, ambil screenshot request yang tokennya sudah dikosongkan, respons 403, dan output pengujian Selenium. Tutupi nilai cookie dan kredensial sebelum membagikan screenshot.

HTTP pada loopback dipakai untuk demonstrasi lokal. Aplikasi publik perlu HTTPS agar data terlindungi saat transit. Kemampuan Burp membaca HTTPS melalui browser yang mempercayai proxy pengujian tidak berarti HTTPS dapat dibaca sembarang perantara. CSRF juga tidak menggantikan HTTPS; [dokumentasi Django](https://docs.djangoproject.com/en/5.2/ref/csrf/) menjelaskan batas perlindungannya.

## Bila pengujian berhenti

| Gejala | Langkah berikutnya |
| --- | --- |
| `No module named selenium` | Instal `requirements-dev.txt` dengan Python environment yang sama dengan perintah menjalankan tes. |
| Driver/browser tidak ditemukan atau tidak cocok | Pastikan browser pilihan tersedia dan koneksi untuk Selenium Manager dapat digunakan; coba `--browser edge` bila Edge sudah tersedia. |
| Halaman browser Burp terus menunggu | Periksa request tertahan di Proxy, lakukan Forward, lalu ubah ke Intercept off. |
| Form tambah proyek menampilkan Forbidden sebelum submit | Login dengan akun yang memiliki `is_superuser=True`; akun biasa memang ditolak. |
| POST masih berhasil setelah manipulasi | Pastikan request yang diubah adalah POST form proyek dan tidak ada token valid di body maupun header `X-CSRFToken`. Periksa respons request itu pada HTTP history. |

PWS tidak diperlukan untuk implementasi atau pemeriksaan lokal ini. Deployment dan bukti pengumpulan di platform kuliah hanya diperlukan jika instruksi pengumpulan memang memintanya; hasil tes lokal tidak memverifikasi kedua hal tersebut.
