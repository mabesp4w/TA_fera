<!-- @format -->

# Quick Start Guide - Database Management

Panduan cepat untuk mengelola database dan import data.

---

## 🚀 Setup Awal

```bash
# 1. Aktifkan virtual environment
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Buat migration (jika ada perubahan model)
python manage.py makemigrations

# 4. Terapkan migration
python manage.py migrate
```

---

## 📝 Migrations

### Membuat Migration

```bash
# Setelah mengubah models.py
python manage.py makemigrations crud

# Dengan nama custom
python manage.py makemigrations crud --name nama_deskriptif
```

### Menerapkan Migration

```bash
# Terapkan semua migration
python manage.py migrate

# Terapkan untuk app tertentu
python manage.py migrate crud

# Cek status migration
python manage.py showmigrations crud
```

---

## 📥 Import Data

### Basic Import

```bash
# Import file Excel
python manage.py import_excel data.xlsx
```

### Test Import (Dry Run)

```bash
# Lihat apa yang akan di-import tanpa menyimpan
python manage.py import_excel data.xlsx --dry-run
```

### Import dengan Options

```bash
# Import dengan skip baris tidak lengkap dan error
python manage.py import_excel data.xlsx \
  --skip-incomplete \
  --skip-errors

# Import dari sheet tertentu
python manage.py import_excel data.xlsx --sheet "Sheet1"

# Import dengan header di baris 2
python manage.py import_excel data.xlsx --start-row 1
```

---

## 🔍 Verifikasi

### Cek Data di Database

```bash
# Buka Django shell
python manage.py shell

# Di shell:
>>> from crud.models import KendaraanBermotor, TransaksiPajak
>>> KendaraanBermotor.objects.count()
>>> TransaksiPajak.objects.count()
>>> KendaraanBermotor.objects.first()
```

---

## ⚠️ Troubleshooting Cepat

| Error                         | Solusi                                    |
| ----------------------------- | ----------------------------------------- |
| `No changes detected`         | Pastikan sudah save `models.py`           |
| `Table already exists`        | `python manage.py migrate --fake-initial` |
| `No polisi diperlukan`        | Pastikan kolom `NO. POLISI` ada di Excel  |
| `Unique constraint violation` | Hapus duplikat di Excel                   |
| `ModuleNotFoundError`         | `pip install -r requirements.txt`         |

---

## 📚 Dokumentasi Lengkap

Lihat `DOCUMENTATION.md` untuk dokumentasi lengkap.

---

**Quick Reference - Last Updated**: 2025-01-XX
