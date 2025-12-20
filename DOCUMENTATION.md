<!-- @format -->

# Dokumentasi Database Management

Dokumentasi lengkap untuk mengelola database Django, termasuk migrations dan import data.

---

## 📋 Daftar Isi

1. [Persiapan](#persiapan)
2. [Migrations](#migrations)
   - [makemigrations](#makemigrations)
   - [migrate](#migrate)
   - [Troubleshooting Migrations](#troubleshooting-migrations)
3. [Import Data](#import-data)
   - [Persiapan File Excel](#persiapan-file-excel)
   - [Command Import](#command-import)
   - [Options dan Flags](#options-dan-flags)
   - [Troubleshooting Import](#troubleshooting-import)
4. [Menghapus Data](#menghapus-data)
   - [Metode 1: Django Shell](#metode-1-menggunakan-django-shell-recommended)
   - [Metode 2: Management Command](#metode-2-menggunakan-management-command-quick)
   - [Metode 3: SQL Langsung](#metode-3-menggunakan-sql-langsung-advanced)

---

## 🚀 Persiapan

### 1. Aktifkan Virtual Environment

```bash
# Aktifkan virtual environment
source .venv/bin/activate

# Atau jika menggunakan venv dengan nama berbeda
source venv/bin/activate
```

### 2. Pastikan Dependencies Terinstall

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Database

Pastikan file `.env` sudah dikonfigurasi dengan benar untuk koneksi database.

#### Format File .env

Buat file `.env` di root project dengan format berikut:

```env
# Database Configuration
DB_NAME=TA_fera
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3309
```

**Catatan**:

- Ganti `your_password` dengan password MySQL Anda
- Port default MySQL adalah `3306`, tapi bisa berbeda (contoh: `3309`)
- Pastikan database sudah dibuat sebelum menjalankan migrations

#### Membuat Database

Jika database belum ada, buat terlebih dahulu:

```bash
# Login ke MySQL
mysql -u root -p -h localhost -P 3309

# Atau jika menggunakan port default
mysql -u root -p
```

Kemudian di MySQL shell:

```sql
CREATE DATABASE TA_fera CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

#### Troubleshooting Koneksi Database

##### Error: "Can't connect to server on 'localhost'"

**Penyebab**: MySQL server tidak berjalan atau konfigurasi koneksi salah.

**Solusi**:

1. **Cek apakah MySQL server berjalan**:

```bash
# Untuk Linux
sudo systemctl status mysql
# atau
sudo service mysql status

# Untuk macOS
brew services list | grep mysql

# Untuk Windows
# Cek di Services atau Task Manager
```

2. **Start MySQL server jika belum berjalan**:

```bash
# Linux
sudo systemctl start mysql
# atau
sudo service mysql start

# macOS
brew services start mysql

# Windows
# Start dari Services atau menggunakan XAMPP/WAMP control panel
```

3. **Verifikasi koneksi manual**:

```bash
# Test koneksi dengan mysql client
mysql -u root -p -h localhost -P 3309

# Jika berhasil, berarti MySQL berjalan
# Jika gagal, cek:
# - Apakah port benar? (default 3306, tapi bisa berbeda)
# - Apakah user dan password benar?
# - Apakah firewall memblokir koneksi?
```

4. **Cek konfigurasi di file .env**:

```bash
# Pastikan file .env ada dan berisi:
cat .env

# Pastikan nilai sesuai dengan konfigurasi MySQL Anda
# DB_HOST=localhost (atau 127.0.0.1)
# DB_PORT=3309 (atau 3306 untuk default)
# DB_USER=root (atau user MySQL Anda)
# DB_PASSWORD=password_anda
# DB_NAME=TA_fera
```

5. **Test koneksi dari Django**:

```bash
# Test koneksi database
python manage.py check --database default

# Atau coba migrate untuk test koneksi
python manage.py migrate --plan
```

##### Error: "Access denied for user"

**Penyebab**: Username atau password salah.

**Solusi**:

```bash
# 1. Verifikasi user dan password di .env
# 2. Test login manual
mysql -u root -p -h localhost -P 3309

# 3. Jika perlu, reset password MySQL
# (Hati-hati, ini akan mengubah password)
```

##### Error: "Unknown database"

**Penyebab**: Database belum dibuat.

**Solusi**:

```bash
# Buat database (lihat bagian "Membuat Database" di atas)
mysql -u root -p -h localhost -P 3309
# CREATE DATABASE TA_fera;
```

##### Error: "Port 3309 connection refused"

**Penyebab**: MySQL tidak berjalan di port tersebut atau port salah.

**Solusi**:

```bash
# 1. Cek port yang digunakan MySQL
sudo netstat -tlnp | grep mysql
# atau
sudo ss -tlnp | grep mysql

# 2. Cek konfigurasi MySQL (my.cnf atau my.ini)
# Lokasi file:
# Linux: /etc/mysql/my.cnf atau /etc/my.cnf
# macOS: /usr/local/etc/my.cnf
# Windows: C:\ProgramData\MySQL\MySQL Server X.X\my.ini

# 3. Pastikan port di .env sesuai dengan port MySQL
```

##### Error saat menggunakan `dbshell`

Jika `python manage.py dbshell` gagal, gunakan alternatif:

```bash
# Gunakan mysql client langsung
mysql -u root -p -h localhost -P 3309 TA_fera

# Atau gunakan Django shell untuk query
python manage.py shell
```

Di Django shell:

```python
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT 1")
cursor.fetchone()
```

---

## 🔄 Migrations

Migrations adalah cara Django untuk mengelola perubahan schema database secara version-controlled.

### makemigrations

**Fungsi**: Membuat file migration baru berdasarkan perubahan model di `models.py`.

#### Basic Usage

```bash
# Membuat migration untuk semua apps
python manage.py makemigrations

# Membuat migration untuk app tertentu
python manage.py makemigrations crud

# Membuat migration dengan nama custom
python manage.py makemigrations crud --name nama_migration
```

#### Options

- `--name <nama>`: Beri nama custom untuk migration file
- `--empty`: Buat migration file kosong (untuk data migration manual)
- `--dry-run`: Tampilkan apa yang akan dibuat tanpa benar-benar membuat file
- `--merge`: Merge migration yang konflik
- `--check`: Cek apakah ada perubahan model yang belum di-migrate

#### Contoh Penggunaan

```bash
# 1. Setelah mengubah models.py, buat migration
python manage.py makemigrations crud

# 2. Buat migration dengan nama deskriptif
python manage.py makemigrations crud --name add_new_field_to_model

# 3. Buat empty migration untuk data migration
python manage.py makemigrations crud --empty --name migrate_existing_data

# 4. Cek apakah ada perubahan yang belum di-migrate
python manage.py makemigrations --check
```

#### Output yang Diharapkan

```
Migrations for 'crud':
  crud/migrations/0005_nama_migration.py
    - Add field new_field to modelname
    - Remove field old_field from modelname
```

#### Kapan Menggunakan makemigrations?

- ✅ Setelah mengubah model di `models.py`
- ✅ Setelah menambah/menghapus field
- ✅ Setelah mengubah tipe data field
- ✅ Setelah menambah/menghapus model
- ✅ Setelah mengubah relasi (ForeignKey, OneToOne, ManyToMany)

---

### migrate

**Fungsi**: Menerapkan migration ke database (membuat/mengubah tabel, kolom, dll).

#### Basic Usage

```bash
# Terapkan semua migration yang belum di-apply
python manage.py migrate

# Terapkan migration untuk app tertentu
python manage.py migrate crud

# Terapkan migration spesifik
python manage.py migrate crud 0004_remove_upt
```

#### Options

- `--fake`: Tandai migration sebagai sudah di-apply tanpa benar-benar menjalankannya
- `--fake-initial`: Fake initial migration jika tabel sudah ada
- `--run-syncdb`: Buat tabel untuk apps yang tidak punya migration
- `--plan`: Tampilkan rencana migration yang akan dijalankan
- `--check`: Cek apakah ada migration yang belum di-apply

#### Contoh Penggunaan

```bash
# 1. Terapkan semua migration
python manage.py migrate

# 2. Terapkan migration untuk app crud saja
python manage.py migrate crud

# 3. Lihat rencana migration yang akan dijalankan
python manage.py migrate --plan

# 4. Cek status migration
python manage.py migrate --check

# 5. Rollback ke migration tertentu (dengan membuat migration baru)
# Catatan: Django tidak punya rollback langsung, harus membuat migration baru
```

#### Output yang Diharapkan

```
Operations to perform:
  Apply all migrations: crud
Running migrations:
  Applying crud.0004_remove_upt... OK
  Applying crud.0005_add_new_field... OK
```

#### Kapan Menggunakan migrate?

- ✅ Setelah membuat migration baru dengan `makemigrations`
- ✅ Setelah pull code dari repository yang punya migration baru
- ✅ Setelah reset database dan ingin setup ulang
- ✅ Setelah deploy ke production

---

### Workflow Migrations Lengkap

#### Skenario 1: Menambah Field Baru

```bash
# 1. Edit models.py, tambahkan field baru
# Contoh: di KendaraanBermotor, tambahkan field 'warna'

# 2. Buat migration
python manage.py makemigrations crud --name add_warna_to_kendaraan

# 3. Review file migration yang dibuat
# File: crud/migrations/0005_add_warna_to_kendaraan.py

# 4. Terapkan migration
python manage.py migrate crud

# 5. Verifikasi di database
python manage.py dbshell
# SQL: DESCRIBE kendaraan_bermotor;
```

#### Skenario 2: Menghapus Field

```bash
# 1. Edit models.py, hapus field yang tidak diperlukan

# 2. Buat migration
python manage.py makemigrations crud

# 3. Terapkan migration
python manage.py migrate crud
```

#### Skenario 3: Setup Database Baru

```bash
# 1. Buat semua migration dari awal
python manage.py makemigrations

# 2. Terapkan semua migration
python manage.py migrate

# 3. Buat superuser (jika diperlukan)
python manage.py createsuperuser
```

---

### Troubleshooting Migrations

#### Error: "No changes detected"

**Penyebab**: Tidak ada perubahan di model yang terdeteksi.

**Solusi**:

- Pastikan sudah menyimpan file `models.py`
- Pastikan tidak ada syntax error di `models.py`
- Cek apakah perubahan sudah ada di migration sebelumnya

#### Error: "Migration dependencies reference nonexistent parent"

**Penyebab**: Migration file mereferensikan migration yang tidak ada.

**Solusi**:

```bash
# Lihat dependency migration
python manage.py showmigrations crud

# Jika ada migration yang hilang, buat ulang atau hapus migration yang bermasalah
```

#### Error: "Table already exists"

**Penyebab**: Tabel sudah ada di database tapi migration belum di-apply.

**Solusi**:

```bash
# Fake initial migration
python manage.py migrate --fake-initial

# Atau hapus tabel dan jalankan migrate lagi (HATI-HATI: akan kehilangan data!)
```

#### Error: "django.db.utils.OperationalError: no such column"

**Penyebab**: Database tidak sinkron dengan model.

**Solusi**:

```bash
# 1. Cek migration yang sudah di-apply
python manage.py showmigrations crud

# 2. Terapkan migration yang belum di-apply
python manage.py migrate crud

# 3. Jika masih error, mungkin perlu reset migration (HATI-HATI!)
```

#### Konflik Migration

**Penyebab**: Dua branch berbeda membuat migration dengan nomor yang sama.

**Solusi**:

```bash
# Merge migration yang konflik
python manage.py makemigrations --merge

# Terapkan migration yang sudah di-merge
python manage.py migrate
```

#### Reset Migration (HATI-HATI - Hanya untuk Development!)

```bash
# 1. Hapus semua migration files (kecuali __init__.py)
# rm crud/migrations/0*.py

# 2. Hapus tabel di database
# python manage.py dbshell
# DROP TABLE ...;

# 3. Buat migration baru
python manage.py makemigrations

# 4. Terapkan migration
python manage.py migrate
```

---

## 📥 Import Data

Import data dari file Excel ke database menggunakan management command `import_excel`.

### Persiapan File Excel

#### Format File

- **Format**: `.xlsx` (Excel 2007+)
- **Encoding**: UTF-8
- **Header**: Baris pertama harus berisi nama kolom

#### Kolom Wajib

File Excel harus memiliki kolom berikut (nama kolom case-insensitive):

**Untuk Kendaraan Bermotor:**

- `NO. POLISI` / `NO_POLISI` / `NOPOL` - **WAJIB**
- `NO. RANGKA` / `NO_RANGKA` - **WAJIB**
- `NO. MESIN` / `NO_MESIN` - **WAJIB**
- `NAMA` - Nama pemilik/wajib pajak - **WAJIB**
- `JENIS KB` / `JENIS` - Jenis kendaraan - **WAJIB**
- `MEREK KB` / `MEREK` - Merek kendaraan - **WAJIB**

**Untuk Transaksi Pajak:**

- `TAHUN` - Tahun transaksi
- `BULAN` - Bulan transaksi
- `TGL. PAJAK` / `TGL_PAJAK` - Tanggal pajak
- `TGL BAYAR` / `TGL_BAYAR` - Tanggal pembayaran

#### Kolom Lainnya (Opsional)

Lihat dokumentasi lengkap di `crud/management/commands/README_IMPORT.md` untuk daftar lengkap kolom yang didukung.

---

### Command Import

#### Basic Usage

```bash
# Import file Excel
python manage.py import_excel <path_to_file.xlsx>

# Contoh
python manage.py import_excel data.xlsx
python manage.py import_excel /path/to/data.xlsx
```

#### Options dan Flags

| Option                 | Deskripsi                                        | Contoh                              |
| ---------------------- | ------------------------------------------------ | ----------------------------------- |
| `--sheet <nama/index>` | Tentukan sheet yang akan dibaca (default: 0)     | `--sheet "Sheet1"` atau `--sheet 1` |
| `--start-row <row>`    | Baris mulai membaca data (0-indexed, default: 0) | `--start-row 1`                     |
| `--dry-run`            | Jalankan tanpa menyimpan ke database             | `--dry-run`                         |
| `--skip-errors`        | Lanjutkan import meskipun ada error              | `--skip-errors`                     |
| `--skip-incomplete`    | Skip baris yang tidak lengkap                    | `--skip-incomplete`                 |

#### Contoh Penggunaan Lengkap

##### 1. Import Standar

```bash
python manage.py import_excel data.xlsx
```

##### 2. Test Import (Dry Run)

```bash
# Lihat apa yang akan di-import tanpa menyimpan
python manage.py import_excel data.xlsx --dry-run
```

**Output:**

```
Dry run mode - tidak ada data yang disimpan
Processing row 1...
  - Kendaraan: DS1007DZ
  - Wajib Pajak: PEMERINTAH KAB. PUNCAK
  - Transaksi: 2022-12
...
Total: 100 rows processed
```

##### 3. Import dari Sheet Tertentu

```bash
# Import dari sheet "Data Kendaraan"
python manage.py import_excel data.xlsx --sheet "Data Kendaraan"

# Import dari sheet index 2 (sheet ketiga)
python manage.py import_excel data.xlsx --sheet 2
```

##### 4. Import dengan Header di Baris 2

```bash
# Jika baris 1 adalah header, baris 2 mulai data
python manage.py import_excel data.xlsx --start-row 1
```

##### 5. Import dengan Skip Error

```bash
# Lanjutkan import meskipun ada baris yang error
python manage.py import_excel data.xlsx --skip-errors
```

##### 6. Import dengan Skip Baris Tidak Lengkap

```bash
# Skip baris yang tidak memiliki data lengkap
python manage.py import_excel data.xlsx --skip-incomplete
```

##### 7. Kombinasi Options

```bash
# Import dengan semua options
python manage.py import_excel data.xlsx \
  --sheet "Sheet1" \
  --start-row 1 \
  --skip-incomplete \
  --skip-errors
```

---

## 🗑️ Menghapus Data

Sebelum melakukan import Excel ulang, Anda mungkin perlu menghapus seluruh data yang ada di database. Berikut adalah cara-cara untuk menghapus data.

### ⚠️ PERINGATAN

**HATI-HATI!** Menghapus data akan menghilangkan semua data secara permanen. Pastikan Anda:

- ✅ Sudah membuat backup database jika data penting
- ✅ Hanya melakukan ini di environment development/testing
- ✅ Memahami bahwa operasi ini tidak dapat di-undo

### Metode 1: Menggunakan Django Shell (Recommended)

Cara paling aman dan terstruktur untuk menghapus data dengan memperhatikan foreign key constraints.

```bash
# Buka Django shell
python manage.py shell
```

Kemudian jalankan script berikut di shell:

```python
from crud.models import (
    TransaksiPajak, DataPajakKendaraan, KendaraanBermotor,
    WajibPajak, Kelurahan, Kecamatan,
    TypeKendaraan, MerekKendaraan, JenisKendaraan,
    AgregatPendapatanBulanan, HasilPrediksi
)

# Hapus data dengan urutan yang benar (menghindari foreign key constraint errors)

# 1. Hapus transaksi dan data terkait
print("Menghapus TransaksiPajak...")
TransaksiPajak.objects.all().delete()

print("Menghapus DataPajakKendaraan...")
DataPajakKendaraan.objects.all().delete()

print("Menghapus AgregatPendapatanBulanan...")
AgregatPendapatanBulanan.objects.all().delete()

print("Menghapus HasilPrediksi...")
HasilPrediksi.objects.all().delete()

# 2. Hapus kendaraan
print("Menghapus KendaraanBermotor...")
KendaraanBermotor.objects.all().delete()

# 3. Hapus wajib pajak
print("Menghapus WajibPajak...")
WajibPajak.objects.all().delete()

# 4. Hapus kelurahan dan kecamatan
print("Menghapus Kelurahan...")
Kelurahan.objects.all().delete()

print("Menghapus Kecamatan...")
Kecamatan.objects.all().delete()

# 5. Hapus type, merek, dan jenis kendaraan
print("Menghapus TypeKendaraan...")
TypeKendaraan.objects.all().delete()

print("Menghapus MerekKendaraan...")
MerekKendaraan.objects.all().delete()

print("Menghapus JenisKendaraan...")
JenisKendaraan.objects.all().delete()

print("\n✅ Semua data berhasil dihapus!")
```

**Output yang Diharapkan:**

```
Menghapus TransaksiPajak...
Menghapus DataPajakKendaraan...
Menghapus AgregatPendapatanBulanan...
Menghapus HasilPrediksi...
Menghapus KendaraanBermotor...
Menghapus WajibPajak...
Menghapus Kelurahan...
Menghapus Kecamatan...
Menghapus TypeKendaraan...
Menghapus MerekKendaraan...
Menghapus JenisKendaraan...

✅ Semua data berhasil dihapus!
```

### Metode 2: Menggunakan Management Command (Quick)

Untuk kemudahan, Anda bisa membuat script Python sederhana atau menjalankan perintah langsung:

```bash
# Buat file clear_data.py
cat > clear_data.py << 'EOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fera.settings')
django.setup()

from crud.models import (
    TransaksiPajak, DataPajakKendaraan, KendaraanBermotor,
    WajibPajak, Kelurahan, Kecamatan,
    TypeKendaraan, MerekKendaraan, JenisKendaraan,
    AgregatPendapatanBulanan, HasilPrediksi
)

# Hapus dengan urutan yang benar
TransaksiPajak.objects.all().delete()
DataPajakKendaraan.objects.all().delete()
AgregatPendapatanBulanan.objects.all().delete()
HasilPrediksi.objects.all().delete()
KendaraanBermotor.objects.all().delete()
WajibPajak.objects.all().delete()
Kelurahan.objects.all().delete()
Kecamatan.objects.all().delete()
TypeKendaraan.objects.all().delete()
MerekKendaraan.objects.all().delete()
JenisKendaraan.objects.all().delete()

print("✅ Semua data berhasil dihapus!")
EOF

# Jalankan script
python clear_data.py

# Hapus file script setelah selesai
rm clear_data.py
```

### Metode 3: Menggunakan SQL Langsung (Advanced)

Jika Anda yakin dengan apa yang Anda lakukan, bisa menggunakan SQL langsung:

```bash
# Buka database shell
python manage.py dbshell
```

Kemudian jalankan SQL berikut (untuk PostgreSQL):

```sql
-- Hapus data dengan urutan yang benar
TRUNCATE TABLE transaksi_pajak CASCADE;
TRUNCATE TABLE data_pajak_kendaraan CASCADE;
TRUNCATE TABLE agregat_pendapatan_bulanan CASCADE;
TRUNCATE TABLE hasil_prediksi CASCADE;
TRUNCATE TABLE kendaraan_bermotor CASCADE;
TRUNCATE TABLE wajib_pajak CASCADE;
TRUNCATE TABLE kelurahan CASCADE;
TRUNCATE TABLE kecamatan CASCADE;
TRUNCATE TABLE type_kendaraan CASCADE;
TRUNCATE TABLE merek_kendaraan CASCADE;
TRUNCATE TABLE jenis_kendaraan CASCADE;
```

Atau untuk SQLite/MySQL:

```sql
-- Hapus dengan DELETE (lebih aman untuk foreign key)
DELETE FROM transaksi_pajak;
DELETE FROM data_pajak_kendaraan;
DELETE FROM agregat_pendapatan_bulanan;
DELETE FROM hasil_prediksi;
DELETE FROM kendaraan_bermotor;
DELETE FROM wajib_pajak;
DELETE FROM kelurahan;
DELETE FROM kecamatan;
DELETE FROM type_kendaraan;
DELETE FROM merek_kendaraan;
DELETE FROM jenis_kendaraan;
```

### Verifikasi Data Terhapus

Setelah menghapus data, verifikasi dengan:

```bash
python manage.py shell
```

```python
from crud.models import (
    TransaksiPajak, DataPajakKendaraan, KendaraanBermotor,
    WajibPajak, Kelurahan, Kecamatan,
    TypeKendaraan, MerekKendaraan, JenisKendaraan
)

# Cek jumlah data
print(f"TransaksiPajak: {TransaksiPajak.objects.count()}")
print(f"DataPajakKendaraan: {DataPajakKendaraan.objects.count()}")
print(f"KendaraanBermotor: {KendaraanBermotor.objects.count()}")
print(f"WajibPajak: {WajibPajak.objects.count()}")
print(f"Kelurahan: {Kelurahan.objects.count()}")
print(f"Kecamatan: {Kecamatan.objects.count()}")
print(f"TypeKendaraan: {TypeKendaraan.objects.count()}")
print(f"MerekKendaraan: {MerekKendaraan.objects.count()}")
print(f"JenisKendaraan: {JenisKendaraan.objects.count()}")
```

Semua seharusnya menampilkan `0`.

### Workflow Lengkap: Hapus Data + Import Baru

```bash
# 1. Hapus semua data (gunakan Metode 1 atau 2)
python manage.py shell
# ... jalankan script penghapusan data ...

# 2. Verifikasi data sudah terhapus
python manage.py shell
# ... cek jumlah data ...

# 3. Import data baru
python manage.py import_excel data.xlsx --skip-incomplete --skip-errors

# 4. Verifikasi data ter-import
python manage.py shell
# ... cek jumlah data yang baru ...
```

---

### Workflow Import Lengkap

#### Skenario 1: Import Data Baru

```bash
# 1. Siapkan file Excel dengan format yang benar

# 2. (Opsional) Hapus data lama jika ingin import ulang dari awal
# Lihat section "Menghapus Data" di atas

# 3. Test import dengan dry-run
python manage.py import_excel data.xlsx --dry-run

# 4. Jika hasil dry-run OK, import sebenarnya
python manage.py import_excel data.xlsx --skip-incomplete --skip-errors

# 5. Verifikasi data di database
python manage.py shell
>>> from crud.models import KendaraanBermotor, TransaksiPajak
>>> KendaraanBermotor.objects.count()
>>> TransaksiPajak.objects.count()
```

#### Skenario 1a: Import Data Baru dengan Hapus Data Lama Terlebih Dahulu

```bash
# 1. Hapus semua data lama
python manage.py shell
# ... jalankan script penghapusan dari section "Menghapus Data" ...

# 2. Siapkan file Excel dengan format yang benar

# 3. Test import dengan dry-run
python manage.py import_excel data.xlsx --dry-run

# 4. Jika hasil dry-run OK, import sebenarnya
python manage.py import_excel data.xlsx --skip-incomplete --skip-errors

# 5. Verifikasi data di database
python manage.py shell
>>> from crud.models import KendaraanBermotor, TransaksiPajak
>>> KendaraanBermotor.objects.count()
>>> TransaksiPajak.objects.count()
```

#### Skenario 2: Import Data Besar

```bash
# Untuk file besar, gunakan skip-errors untuk menghindari rollback total
python manage.py import_excel large_data.xlsx \
  --skip-incomplete \
  --skip-errors

# Monitor progress (script akan menampilkan progress setiap 100 rows)
```

#### Skenario 3: Update Data Existing

```bash
# Script akan otomatis update jika no_polisi sudah ada
python manage.py import_excel updated_data.xlsx
```

---

### Troubleshooting Import

#### Error: "No polisi diperlukan"

**Penyebab**: Kolom nomor polisi tidak ditemukan atau kosong.

**Solusi**:

- Pastikan kolom `NO. POLISI` atau variasi namanya ada di Excel
- Pastikan data tidak kosong untuk kolom wajib
- Gunakan `--skip-incomplete` untuk skip baris yang tidak lengkap

#### Error: "Jenis kendaraan diperlukan"

**Penyebab**: Kolom jenis kendaraan tidak ditemukan atau kosong.

**Solusi**:

```bash
# Gunakan --skip-incomplete untuk skip baris yang tidak lengkap
python manage.py import_excel data.xlsx --skip-incomplete
```

#### Error: "Unique constraint violation"

**Penyebab**: Ada duplikat `no_polisi` atau `no_rangka` di Excel atau database.

**Solusi**:

- Hapus duplikat di Excel sebelum import
- Atau update data existing dengan import ulang (script akan update jika `no_polisi` sudah ada)

#### Error: "Kabupaten asal diperlukan"

**Penyebab**: Kolom kabupaten/kota tidak ditemukan atau tidak valid.

**Solusi**:

- Pastikan kolom `KAB./KOTA` atau `KABUPATEN` ada di Excel
- Pastikan nilai tidak kosong atau numeric (akan di-skip)

#### Error: "ModuleNotFoundError: No module named 'pandas'"

**Penyebab**: Dependencies belum terinstall.

**Solusi**:

```bash
pip install -r requirements.txt
```

#### Data Tidak Ter-import

**Penyebab**: Format kolom tidak sesuai atau data kosong.

**Solusi**:

```bash
# 1. Test dengan dry-run untuk melihat apa yang terdeteksi
python manage.py import_excel data.xlsx --dry-run

# 2. Periksa format kolom sesuai dokumentasi
# 3. Pastikan data tidak kosong untuk kolom wajib
# 4. Gunakan --skip-incomplete jika ada baris yang tidak lengkap
```

#### Tanggal Tidak Ter-import dengan Benar

**Penyebab**: Format tanggal di Excel tidak dikenali.

**Solusi**:

- Pastikan tanggal dalam format yang valid (YYYY-MM-DD atau format Excel standar)
- Script akan otomatis mengkonversi Excel date serial number
- Jika masih error, periksa format tanggal di Excel

#### Progress Tidak Tampil untuk File Besar

**Penyebab**: Script menampilkan progress setiap 100 rows.

**Solusi**:

- Tunggu hingga selesai, progress akan tampil setiap 100 rows
- Untuk file sangat besar, pertimbangkan split file menjadi beberapa bagian

---

## 📚 Best Practices

### Migrations

1. **Selalu Review Migration File**

   - Sebelum apply migration, review file migration yang dibuat
   - Pastikan perubahan sesuai yang diinginkan

2. **Commit Migration Files**

   - Selalu commit migration files ke version control
   - Jangan hapus migration files yang sudah di-apply di production

3. **Test Migration di Development**

   - Selalu test migration di development sebelum apply ke production
   - Buat backup database sebelum apply migration di production

4. **Gunakan Nama Deskriptif**
   - Gunakan `--name` untuk memberi nama migration yang jelas
   - Contoh: `--name add_warna_to_kendaraan`

### Import Data

1. **Selalu Dry-Run Dulu**

   - Gunakan `--dry-run` untuk test sebelum import sebenarnya
   - Verifikasi data yang akan di-import sesuai ekspektasi

2. **Backup Database**

   - Buat backup database sebelum import data besar
   - Siapkan rollback plan jika ada masalah

3. **Validasi Data Excel**

   - Pastikan format Excel sesuai dokumentasi
   - Bersihkan data duplikat sebelum import
   - Pastikan kolom wajib tidak kosong

4. **Monitor Progress**

   - Untuk file besar, monitor progress import
   - Gunakan `--skip-errors` untuk menghindari rollback total

5. **Verifikasi Setelah Import**
   - Verifikasi jumlah data yang ter-import
   - Cek beberapa sample data untuk memastikan akurasi

---

## 🔗 Referensi

- **Django Migrations**: https://docs.djangoproject.com/en/stable/topics/migrations/
- **Import Excel Command**: `crud/management/commands/README_IMPORT.md`
- **Django Management Commands**: https://docs.djangoproject.com/en/stable/howto/custom-management-commands/

---

## 🔧 Troubleshooting Umum

### Masalah Koneksi Database

Lihat section [Troubleshooting Koneksi Database](#troubleshooting-koneksi-database) di bagian Persiapan untuk solusi lengkap.

### Masalah Migrations

Lihat section [Troubleshooting Migrations](#troubleshooting-migrations) untuk masalah terkait migrations.

### Masalah Import Data

Lihat section [Troubleshooting Import](#troubleshooting-import) untuk masalah terkait import Excel.

### Checklist Troubleshooting

Sebelum mencari bantuan, pastikan Anda sudah:

- ✅ Memeriksa error message dengan detail
- ✅ Memverifikasi konfigurasi database di `.env`
- ✅ Memastikan MySQL server berjalan
- ✅ Memastikan database sudah dibuat
- ✅ Memastikan semua dependencies terinstall (`pip install -r requirements.txt`)
- ✅ Memastikan virtual environment aktif
- ✅ Mencoba dengan `--dry-run` untuk test tanpa menyimpan data
- ✅ Memeriksa log Django untuk detail error

---

## 📞 Bantuan

Jika mengalami masalah:

1. Cek dokumentasi troubleshooting di atas
2. Review error message dengan detail
3. Gunakan `--dry-run` untuk test tanpa menyimpan data
4. Cek log Django untuk detail error
5. Pastikan semua dependencies terinstall dengan benar
6. Verifikasi koneksi database dengan `python manage.py check --database default`

---

**Last Updated**: 2025-01-XX
**Version**: 1.0
