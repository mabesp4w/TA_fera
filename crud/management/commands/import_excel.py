"""
Management command untuk import data dari Excel ke database
Usage: python manage.py import_excel <file_path> [--sheet <sheet_name>] [--start-row <row>] [--dry-run]
"""

import pandas as pd
import re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_date
from decimal import Decimal, InvalidOperation
from datetime import datetime
import os

from crud.models import (
    Kecamatan, Kelurahan, JenisKendaraan, MerekKendaraan, TypeKendaraan,
    WajibPajak, KendaraanBermotor, DataPajakKendaraan, TransaksiPajak
)


class Command(BaseCommand):
    help = 'Import data dari file Excel ke database'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path ke file Excel')
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,
            help='Nama sheet atau index sheet (default: 0)'
        )
        parser.add_argument(
            '--start-row',
            type=int,
            default=0,
            help='Baris mulai membaca data (default: 0, header di baris pertama)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Jalankan tanpa menyimpan ke database (untuk testing)'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Lanjutkan import meskipun ada error pada baris tertentu'
        )
        parser.add_argument(
            '--skip-incomplete',
            action='store_true',
            help='Skip baris yang tidak lengkap (missing required fields)'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        sheet = options['sheet']
        start_row = options['start_row']
        dry_run = options['dry_run']
        skip_errors = options['skip_errors']
        skip_incomplete = options['skip_incomplete']

        # Validasi file
        if not os.path.exists(file_path):
            raise CommandError(f'File tidak ditemukan: {file_path}')

        self.stdout.write(self.style.SUCCESS(f'Memulai import dari: {file_path}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - Tidak ada data yang akan disimpan'))

        try:
            # Baca Excel file
            self.stdout.write('Membaca file Excel...')
            df = pd.read_excel(file_path, sheet_name=sheet, header=start_row)
            self.stdout.write(self.style.SUCCESS(f'Berhasil membaca {len(df)} baris data'))

            # Normalisasi nama kolom (lowercase, strip whitespace, replace space dengan underscore)
            # Juga handle format Excel Indonesia dengan titik dan strip
            df.columns = (
                df.columns.str.lower()
                .str.strip()
                .str.replace(' ', '_')
                .str.replace('-', '_')
                .str.replace('.', '_')
                .str.replace('/', '_')
                .str.replace('(', '')
                .str.replace(')', '')
            )

            # Import data
            stats = {
                'created': 0,
                'updated': 0,
                'errors': 0,
                'skipped': 0
            }

            if not dry_run:
                with transaction.atomic():
                    self._import_data(df, stats, skip_errors, skip_incomplete)
            else:
                self._import_data(df, stats, skip_errors, skip_incomplete)

            # Tampilkan statistik
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('STATISTIK IMPORT:'))
            self.stdout.write(f'  Created: {stats["created"]}')
            self.stdout.write(f'  Updated: {stats["updated"]}')
            self.stdout.write(f'  Errors: {stats["errors"]}')
            self.stdout.write(f'  Skipped: {stats["skipped"]}')
            self.stdout.write('='*50)

        except Exception as e:
            raise CommandError(f'Error saat import: {str(e)}')

    def _import_data(self, df, stats, skip_errors, skip_incomplete):
        """Import data dari DataFrame"""
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            try:
                # Progress indicator setiap 100 baris atau baris terakhir
                if (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                    self.stdout.write(f'\nProcessing row {idx + 1}/{total_rows}...', ending='')
                
                # Cek apakah baris lengkap (jika skip_incomplete aktif)
                if skip_incomplete and not self._is_row_complete(row):
                    stats['skipped'] += 1
                    if (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                        self.stdout.write(self.style.WARNING(' [SKIPPED - Data tidak lengkap]'))
                    continue
                
                # Import berdasarkan kolom yang ada
                if self._has_kendaraan_columns(row):
                    self._import_kendaraan_and_transaksi(row, stats, skip_incomplete)
                elif self._has_transaksi_only_columns(row):
                    self._import_transaksi_only(row, stats)
                else:
                    stats['skipped'] += 1
                    if (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                        self.stdout.write(self.style.WARNING(' [SKIPPED - Tidak ada kolom yang cocok]'))
                    continue
                
                if (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                    self.stdout.write(self.style.SUCCESS(' [OK]'))
                
            except Exception as e:
                stats['errors'] += 1
                error_msg = f' [ERROR: {str(e)}]'
                if skip_errors:
                    if (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                        self.stdout.write(self.style.ERROR(error_msg))
                    continue
                else:
                    self.stdout.write(f'\nRow {idx + 1}: {error_msg}')
                    raise

    def _has_kendaraan_columns(self, row):
        """Cek apakah row memiliki kolom untuk kendaraan"""
        required = [
            'no_polisi', 'no__polisi', 'nopol',
            'no_rangka', 'no__rangka', 'nomor_rangka'
        ]
        return any(col in row.index for col in required)

    def _has_transaksi_only_columns(self, row):
        """Cek apakah row hanya memiliki kolom transaksi"""
        return 'tahun' in row.index and 'bulan' in row.index

    def _import_kendaraan_and_transaksi(self, row, stats, skip_incomplete=False):
        """Import kendaraan dan transaksi dari satu row"""
        # 1. Import/Create Kecamatan dan Kelurahan (untuk WajibPajak)
        kecamatan = None
        kelurahan = None
        kecamatan = self._get_or_create_kecamatan(row)
        if kecamatan:
            kelurahan = self._get_or_create_kelurahan(row, kecamatan)
        
        # 3. Import/Create WajibPajak
        wajib_pajak = self._get_or_create_wajib_pajak(row, kelurahan)
        
        # 4. Import/Create JenisKendaraan, MerekKendaraan, TypeKendaraan
        jenis = self._get_or_create_jenis_kendaraan(row, skip_incomplete)
        merek = self._get_or_create_merek_kendaraan(row, skip_incomplete)
        type_kendaraan = self._get_or_create_type_kendaraan(row, merek)
        
        # 5. Import/Create KendaraanBermotor
        kendaraan = self._get_or_create_kendaraan(
            row, wajib_pajak, jenis, merek, type_kendaraan, stats, skip_incomplete
        )
        
        # 6. Import/Create DataPajakKendaraan
        self._get_or_create_data_pajak(row, kendaraan, stats)
        
        # 7. Import/Create TransaksiPajak (jika ada data transaksi)
        if self._has_transaksi_data(row):
            self._get_or_create_transaksi(row, kendaraan, stats)

    def _import_transaksi_only(self, row, stats):
        """Import hanya transaksi (kendaraan sudah ada)"""
        no_polisi = (
            self._get_value(row, 'no_polisi') or
            self._get_value(row, 'no__polisi') or
            self._get_value(row, 'nopol')
        )
        if not no_polisi:
            raise ValueError('no_polisi diperlukan untuk import transaksi')
        
        try:
            kendaraan = KendaraanBermotor.objects.get(no_polisi=str(no_polisi))
        except KendaraanBermotor.DoesNotExist:
            raise ValueError(f'Kendaraan dengan no_polisi {no_polisi} tidak ditemukan')
        
        self._get_or_create_transaksi(row, kendaraan, stats)

    # ========== Helper Methods untuk Get or Create ==========

    def _get_or_create_kecamatan(self, row):
        """Get or create Kecamatan"""
        nama = self._get_value(row, 'kecamatan')
        
        if not nama:
            return None
        
        nama_clean = str(nama).strip()
        kecamatan, created = Kecamatan.objects.get_or_create(
            nama=nama_clean
        )
        return kecamatan
    
    def _get_or_create_kelurahan(self, row, kecamatan):
        """Get or create Kelurahan"""
        nama = self._get_value(row, 'kelurahan')
        
        if not nama or not kecamatan:
            return None
        
        nama_clean = str(nama).strip()
        kelurahan, created = Kelurahan.objects.get_or_create(
            kecamatan=kecamatan,
            nama=nama_clean
        )
        return kelurahan

    def _get_or_create_wajib_pajak(self, row, kelurahan=None):
        """Get or create WajibPajak"""
        no_ktp = (
            self._get_value(row, 'no_ktp') or 
            self._get_value(row, 'ktp') or
            self._get_value(row, 'no_e_ktp') or
            self._get_value(row, 'no_e-ktp') or
            self._get_value(row, 'no__e-ktp') or
            self._get_value(row, 'no__e_ktp')
        )
        nama = (
            self._get_value(row, 'nama') or 
            self._get_value(row, 'nama_wajib_pajak') or 
            self._get_value(row, 'nama_pemilik')
        )
        alamat = (
            self._get_value(row, 'alamat') or 
            self._get_value(row, 'alamat_wp') or
            ''
        )
        
        if not nama:
            raise ValueError('Nama wajib pajak diperlukan')
        
        # Clean no_ktp - remove whitespace, skip if empty
        no_ktp_clean = str(no_ktp).strip() if no_ktp else None
        if no_ktp_clean and not no_ktp_clean:  # Jika setelah strip menjadi empty string
            no_ktp_clean = None
        
        # Cari berdasarkan no_ktp jika ada, atau nama
        if no_ktp_clean:
            wajib_pajak, created = WajibPajak.objects.get_or_create(
                no_ktp=no_ktp_clean,
                defaults={
                    'nama': str(nama).strip(),
                    'alamat': str(alamat).strip(),
                    'kelurahan': kelurahan
                }
            )
            # Update kelurahan jika sudah ada
            if not created and kelurahan:
                wajib_pajak.kelurahan = kelurahan
                wajib_pajak.save()
        else:
            # Jika tidak ada KTP, cari berdasarkan nama
            wajib_pajak = WajibPajak.objects.filter(nama=nama).first()
            if not wajib_pajak:
                wajib_pajak = WajibPajak.objects.create(
                    nama=str(nama).strip(),
                    alamat=str(alamat).strip(),
                    kelurahan=kelurahan
                )
            elif kelurahan:
                wajib_pajak.kelurahan = kelurahan
                wajib_pajak.save()
        
        return wajib_pajak

    def _get_or_create_jenis_kendaraan(self, row, skip_incomplete=False):
        """Get or create JenisKendaraan"""
        nama = (
            self._get_value(row, 'jenis') or 
            self._get_value(row, 'jenis_kendaraan') or
            self._get_value(row, 'jenis_kb')
        )
        
        if not nama:
            if skip_incomplete:
                # Gunakan default jika skip_incomplete
                nama = 'LAINNYA'
            else:
                raise ValueError('Jenis kendaraan diperlukan')
        
        # Clean nama - remove extra spaces
        nama_clean = str(nama).strip()
        
        # Get kategori from Excel or infer from nama
        kategori = self._get_value(row, 'kategori') or self._get_value(row, 'kategori_kendaraan')
        if not kategori:
            # Infer kategori from nama
            kategori = self._infer_kategori_from_nama(nama_clean)
        
        # Normalize kategori to uppercase
        if kategori:
            kategori = str(kategori).strip().upper()
            # Map to valid choices
            kategori_map = {
                'MOTOR': 'MOTOR',
                'SEPEDA MOTOR': 'MOTOR',
                'MOBIL': 'MOBIL',
                'JEEP': 'JEEP',
                'TRUK': 'TRUK',
                'TRUCK': 'TRUK',
                'BUS': 'BUS',
                'LAINNYA': 'LAINNYA',
                'LAIN-LAIN': 'LAINNYA',
            }
            kategori = kategori_map.get(kategori, 'MOTOR')  # Default to MOTOR if not recognized
        
        jenis, created = JenisKendaraan.objects.get_or_create(
            nama=nama_clean,
            defaults={'kategori': kategori}
        )
        
        # Update kategori if jenis sudah ada dan kategori berbeda
        if not created and kategori and jenis.kategori != kategori:
            jenis.kategori = kategori
            jenis.save()
        
        return jenis
    
    def _infer_kategori_from_nama(self, nama):
        """Infer kategori kendaraan dari nama jenis"""
        nama_lower = str(nama).lower()
        
        # Keywords untuk setiap kategori
        if any(keyword in nama_lower for keyword in ['mobil', 'sedan', 'hatchback', 'suv', 'mpv', 'minibus', 'city car']):
            return 'MOBIL'
        elif any(keyword in nama_lower for keyword in ['jeep', 'jip']):
            return 'JEEP'
        elif any(keyword in nama_lower for keyword in ['truk', 'truck', 'pick up', 'pickup', 'double cabin']):
            return 'TRUK'
        elif any(keyword in nama_lower for keyword in ['bus', 'bis']):
            return 'BUS'
        elif any(keyword in nama_lower for keyword in ['motor', 'sepeda motor', 'skuter', 'scooter', 'moped']):
            return 'MOTOR'
        else:
            # Default to MOTOR jika tidak bisa di-infer
            return 'MOTOR'

    def _get_or_create_merek_kendaraan(self, row, skip_incomplete=False):
        """Get or create MerekKendaraan"""
        nama = (
            self._get_value(row, 'merek') or 
            self._get_value(row, 'merek_kendaraan') or
            self._get_value(row, 'merek_kb')
        )
        
        if not nama:
            if skip_incomplete:
                # Gunakan default jika skip_incomplete
                nama = 'TIDAK DIKETAHUI'
            else:
                raise ValueError('Merek kendaraan diperlukan')
        
        merek, created = MerekKendaraan.objects.get_or_create(nama=str(nama))
        return merek

    def _get_or_create_type_kendaraan(self, row, merek):
        """Get or create TypeKendaraan"""
        nama = (
            self._get_value(row, 'type') or 
            self._get_value(row, 'type_kendaraan') or 
            self._get_value(row, 'tipe') or
            self._get_value(row, 'type_kb')
        )
        
        if not nama:
            # Default type jika tidak ada
            nama = 'Default'
        
        type_kendaraan, created = TypeKendaraan.objects.get_or_create(
            merek=merek,
            nama=str(nama),
            defaults={}
        )
        return type_kendaraan

    def _get_or_create_kendaraan(self, row, wajib_pajak, jenis, merek, type_kendaraan, stats, skip_incomplete=False):
        """
        Get or create KendaraanBermotor
        
        Catatan: Jika no_polisi sudah ada, akan menggunakan kendaraan yang sama.
        Ini memungkinkan multiple transaksi untuk kendaraan yang sama (dengan tahun/bulan berbeda).
        """
        no_polisi = (
            self._get_value(row, 'no_polisi') or 
            self._get_value(row, 'nopol') or
            self._get_value(row, 'no__polisi')
        )
        if not no_polisi:
            raise ValueError('No polisi diperlukan')
        
        no_rangka = (
            self._get_value(row, 'no_rangka') or 
            self._get_value(row, 'nomor_rangka') or
            self._get_value(row, 'no__rangka')
        )
        if not no_rangka:
            raise ValueError('No rangka diperlukan')
        
        no_mesin = (
            self._get_value(row, 'no_mesin') or 
            self._get_value(row, 'nomor_mesin') or
            self._get_value(row, 'no__mesin')
        )
        if not no_mesin:
            raise ValueError('No mesin diperlukan')
        
        # Get values dengan default
        tahun_buat = (
            self._safe_int(row, 'tahun_buat') or 
            self._safe_int(row, 'tahun')
        )
        jml_cc = (
            self._safe_int(row, 'jml_cc') or 
            self._safe_int(row, 'cc') or
            self._safe_int(row, 'jml_cc') or
            0
        )
        bbm = (
            self._get_value(row, 'bbm') or 
            'BENSIN'
        )
        
        kendaraan, created = KendaraanBermotor.objects.get_or_create(
            no_polisi=str(no_polisi),
            defaults={
                'no_rangka': str(no_rangka),
                'no_mesin': str(no_mesin),
                'wajib_pajak': wajib_pajak,
                'jenis': jenis,
                'merek': merek,
                'type_kendaraan': type_kendaraan,
                'tahun_buat': tahun_buat or 2000,
                'jml_cc': jml_cc,
                'bbm': str(bbm),
            }
        )
        
        if created:
            stats['created'] += 1
        else:
            stats['updated'] += 1
        
        return kendaraan

    def _get_or_create_data_pajak(self, row, kendaraan, stats):
        """Get or create DataPajakKendaraan"""
        njkb = (
            self._safe_decimal(row, 'njkb_saat_ini') or 
            self._safe_decimal(row, 'njkb') or
            Decimal('0')
        )
        bobot = (
            self._safe_decimal(row, 'bobot_saat_ini') or 
            self._safe_decimal(row, 'bobot') or
            Decimal('1.0')
        )
        tarif = (
            self._safe_decimal(row, 'tarif_pkb_saat_ini') or 
            self._safe_decimal(row, 'tarif_pkb') or
            Decimal('0')
        )
        
        data_pajak, created = DataPajakKendaraan.objects.get_or_create(
            kendaraan=kendaraan,
            defaults={
                'njkb_saat_ini': njkb,
                'bobot_saat_ini': bobot,
                'tarif_pkb_saat_ini': tarif,
            }
        )
        
        if not created:
            # Update jika sudah ada
            data_pajak.njkb_saat_ini = njkb
            data_pajak.bobot_saat_ini = bobot
            data_pajak.tarif_pkb_saat_ini = tarif
            data_pajak.save()
            stats['updated'] += 1
        else:
            stats['created'] += 1

    def _get_or_create_transaksi(self, row, kendaraan, stats):
        """
        Get or create TransaksiPajak
        
        Catatan: Satu kendaraan dapat memiliki multiple transaksi dengan tahun/bulan berbeda.
        Unique constraint: (kendaraan, tahun, bulan)
        Untuk menambahkan transaksi baru pada kendaraan yang sama, gunakan tahun/bulan yang berbeda.
        """
        tahun = (
            self._safe_int(row, 'tahun') or
            self._safe_int(row, 'tahun_transaksi')
        )
        bulan = (
            self._safe_int(row, 'bulan') or
            self._safe_int(row, 'bulan_transaksi')
        )
        
        if not tahun or not bulan:
            return None
        
        # Parse tanggal - handle berbagai format
        # Prioritas: TGL. PAJAK (tgl__pajak setelah normalisasi), TGL BAYAR TRANSAKSI TERAKHIR
        tgl_pajak = (
            self._parse_date(row, 'tgl__pajak') or  # TGL. PAJAK setelah normalisasi
            self._parse_date(row, 'tgl_pajak') or
            self._parse_date(row, 'tgl_pajak_transaksi_terakhir')
        )
        tgl_bayar = (
            self._parse_date(row, 'tgl_bayar_transaksi_terakhir') or  # TGL BAYAR TRANSAKSI TERAKHIR
            self._parse_date(row, 'tgl_bayar')
        )
        
        # Periode pembayaran
        jml_tahun_bayar = (
            self._safe_int(row, 'jml_tahun_bayar') or
            self._safe_int(row, 'jml_tahun') or
            1
        )
        jml_bulan_bayar = (
            self._safe_int(row, 'jml_bulan_bayar') or
            self._safe_int(row, 'jml_bulan') or
            0
        )
        
        # Amounts - handle format Excel dengan "TRANSAKSI TERAKHIR"
        pokok_pkb = (
            self._safe_decimal(row, 'pokok_pkb') or
            self._safe_decimal(row, 'pokok_pkb_transaksi_terakhir') or
            Decimal('0')
        )
        denda_pkb = (
            self._safe_decimal(row, 'denda_pkb') or
            self._safe_decimal(row, 'denda_pkb_transaksi_terakhir') or
            Decimal('0')
        )
        tunggakan_pokok_pkb = (
            self._safe_decimal(row, 'tunggakan_pokok_pkb') or
            self._safe_decimal(row, 'tunggakan_pokok_pkb_transaksi_terakhir') or
            Decimal('0')
        )
        tunggakan_denda_pkb = (
            self._safe_decimal(row, 'tunggakan_denda_pkb') or
            self._safe_decimal(row, 'tunggakan_denda_pkb_transaksi_terakhir') or
            Decimal('0')
        )
        opsen_pokok_pkb = (
            self._safe_decimal(row, 'opsen_pokok_pkb') or
            self._safe_decimal(row, 'opsen_pokok_pkb_terakhir') or
            Decimal('0')
        )
        opsen_denda_pkb = (
            self._safe_decimal(row, 'opsen_denda_pkb') or
            self._safe_decimal(row, 'opsen_denda_pkb_terakhir') or
            Decimal('0')
        )
        pokok_swdkllj = (
            self._safe_decimal(row, 'pokok_swdkllj') or
            self._safe_decimal(row, 'pokok_sw_transaksi_terakhir') or
            Decimal('0')
        )
        denda_swdkllj = (
            self._safe_decimal(row, 'denda_swdkllj') or
            self._safe_decimal(row, 'denda_sw_transaksi_terakhir') or
            Decimal('0')
        )
        tunggakan_pokok_swdkllj = (
            self._safe_decimal(row, 'tunggakan_pokok_swdkllj') or
            self._safe_decimal(row, 'tunggakan_pokok_sw_transaksi_terakhir') or
            Decimal('0')
        )
        tunggakan_denda_swdkllj = (
            self._safe_decimal(row, 'tunggakan_denda_swdkllj') or
            self._safe_decimal(row, 'tunggakan_denda_sw_transaksi_terakhir') or
            Decimal('0')
        )
        pokok_bbnkb = (
            self._safe_decimal(row, 'pokok_bbnkb') or
            self._safe_decimal(row, 'pokok_bbn_transaksi_terakhir') or
            Decimal('0')
        )
        denda_bbnkb = (
            self._safe_decimal(row, 'denda_bbnkb') or
            self._safe_decimal(row, 'denda_bbn_transaksi_terakhir') or
            Decimal('0')
        )
        opsen_pokok_bbnkb = (
            self._safe_decimal(row, 'opsen_pokok_bbnkb') or
            self._safe_decimal(row, 'opsen_pokok_bbnkb_terakhir') or
            Decimal('0')
        )
        opsen_denda_bbnkb = (
            self._safe_decimal(row, 'opsen_denda_bbnkb') or
            self._safe_decimal(row, 'opsen_denda_bbnkb_terakhir') or
            Decimal('0')
        )
        
        transaksi, created = TransaksiPajak.objects.get_or_create(
            kendaraan=kendaraan,
            tahun=tahun,
            bulan=bulan,
            defaults={
                'tgl_pajak': tgl_pajak,
                'tgl_bayar': tgl_bayar,
                'jml_tahun_bayar': jml_tahun_bayar,
                'jml_bulan_bayar': jml_bulan_bayar,
                'pokok_pkb': pokok_pkb,
                'denda_pkb': denda_pkb,
                'tunggakan_pokok_pkb': tunggakan_pokok_pkb,
                'tunggakan_denda_pkb': tunggakan_denda_pkb,
                'opsen_pokok_pkb': opsen_pokok_pkb,
                'opsen_denda_pkb': opsen_denda_pkb,
                'pokok_swdkllj': pokok_swdkllj,
                'denda_swdkllj': denda_swdkllj,
                'tunggakan_pokok_swdkllj': tunggakan_pokok_swdkllj,
                'tunggakan_denda_swdkllj': tunggakan_denda_swdkllj,
                'pokok_bbnkb': pokok_bbnkb,
                'denda_bbnkb': denda_bbnkb,
                'opsen_pokok_bbnkb': opsen_pokok_bbnkb,
                'opsen_denda_bbnkb': opsen_denda_bbnkb,
            }
        )
        
        # Update tanggal jika transaksi sudah ada (get_or_create hanya set defaults saat create)
        if not created:
            # Update tanggal jika ada nilai baru
            updated = False
            if tgl_pajak:
                transaksi.tgl_pajak = tgl_pajak
                updated = True
            if tgl_bayar:
                transaksi.tgl_bayar = tgl_bayar
                updated = True
            if updated:
                transaksi.save()
            stats['updated'] += 1
        else:
            stats['created'] += 1

    # ========== Helper Methods untuk Parse Data ==========

    def _get_value(self, row, key, default=None):
        """Get value from row dengan berbagai variasi key"""
        if key in row.index:
            value = row[key]
            if pd.isna(value):
                return default
            # Jangan convert ke string jika itu angka (untuk parsing tanggal)
            # Return as-is untuk angka, convert ke string untuk text
            if isinstance(value, (int, float)) or (hasattr(value, 'dtype') and ('int' in str(value.dtype) or 'float' in str(value.dtype))):
                return value
            return str(value).strip() if value else default
        return default

    def _safe_int(self, row, key, default=None):
        """Safely convert to int"""
        value = self._get_value(row, key)
        if value is None:
            return default
        try:
            if isinstance(value, (int, float)):
                return int(value)
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default

    def _safe_decimal(self, row, key, default=None):
        """Safely convert to Decimal"""
        value = self._get_value(row, key)
        if value is None:
            return default
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            # Remove currency symbols and commas
            value_str = str(value).replace('Rp', '').replace(',', '').replace(' ', '').strip()
            return Decimal(value_str)
        except (ValueError, InvalidOperation, TypeError):
            return default

    def _parse_date(self, row, key):
        """Parse date from various formats"""
        value = self._get_value(row, key)
        if value is None:
            return None
        
        # Handle Excel date serial number (prioritas pertama)
        # Bisa berupa int, float, atau numpy int64
        if isinstance(value, (int, float)) or (hasattr(value, 'dtype') and ('int' in str(value.dtype) or 'float' in str(value.dtype))):
            try:
                # Convert to int first
                value_int = int(float(value))
                # Excel date serial number (days since 1900-01-01)
                # Note: Excel counts from 1900-01-01, but has a bug treating 1900 as leap year
                from datetime import datetime, timedelta
                excel_epoch = datetime(1899, 12, 30)
                date_obj = excel_epoch + timedelta(days=value_int)
                return date_obj.date()
            except Exception as e:
                # Jika gagal, coba dengan pandas
                pass
        
        # Try pandas to_datetime (handle Excel dates better)
        try:
            if isinstance(value, pd.Timestamp):
                return value.date()
            # pandas bisa handle Excel serial number juga
            # Coba dengan origin Excel
            if isinstance(value, (int, float)) or (hasattr(value, 'dtype') and ('int' in str(value.dtype) or 'float' in str(value.dtype))):
                date_obj = pd.to_datetime(value, errors='coerce', origin='1899-12-30', unit='D')
            else:
                date_obj = pd.to_datetime(value, errors='coerce')
            
            if pd.notna(date_obj):
                if isinstance(date_obj, pd.Timestamp):
                    return date_obj.date()
                return date_obj
        except:
            pass
        
        # Try parse_date (untuk string format)
        try:
            parsed = parse_date(str(value))
            if parsed:
                return parsed
        except:
            pass
        
        return None

    def _has_transaksi_data(self, row):
        """Check if row has transaksi data"""
        return 'tahun' in row.index and 'bulan' in row.index

    def _is_row_complete(self, row):
        """Check if row has all required fields for kendaraan"""
        required_fields = [
            'no_polisi', 'no__polisi', 'nopol',
            'no_rangka', 'no__rangka', 'nomor_rangka',
            'no_mesin', 'no__mesin', 'nomor_mesin',
            'nama',
            'jenis', 'jenis_kendaraan', 'jenis_kb',
            'merek', 'merek_kendaraan', 'merek_kb'
        ]
        
        # Cek apakah minimal ada satu dari setiap kategori required
        has_no_polisi = any(col in row.index for col in ['no_polisi', 'no__polisi', 'nopol'])
        has_no_rangka = any(col in row.index for col in ['no_rangka', 'no__rangka', 'nomor_rangka'])
        has_no_mesin = any(col in row.index for col in ['no_mesin', 'no__mesin', 'nomor_mesin'])
        has_nama = 'nama' in row.index
        has_jenis = any(col in row.index for col in ['jenis', 'jenis_kendaraan', 'jenis_kb'])
        has_merek = any(col in row.index for col in ['merek', 'merek_kendaraan', 'merek_kb'])
        
        return has_no_polisi and has_no_rangka and has_no_mesin and has_nama and has_jenis and has_merek
