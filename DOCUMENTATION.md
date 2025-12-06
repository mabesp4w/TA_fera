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

### Workflow Import Lengkap

#### Skenario 1: Import Data Baru

```bash
# 1. Siapkan file Excel dengan format yang benar

# 2. Test import dengan dry-run
python manage.py import_excel data.xlsx --dry-run

# 3. Jika hasil dry-run OK, import sebenarnya
python manage.py import_excel data.xlsx --skip-incomplete --skip-errors

# 4. Verifikasi data di database
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

## 📞 Bantuan

Jika mengalami masalah:

1. Cek dokumentasi troubleshooting di atas
2. Review error message dengan detail
3. Gunakan `--dry-run` untuk test tanpa menyimpan data
4. Cek log Django untuk detail error
5. Pastikan semua dependencies terinstall dengan benar

---

**Last Updated**: 2025-01-XX
**Version**: 1.0
