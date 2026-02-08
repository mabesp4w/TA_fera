from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from myauth.models import User
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from crud.models import (
    KendaraanBermotor, TransaksiPajak, WajibPajak,
    JenisKendaraan, Kecamatan, Kelurahan,
    AgregatPendapatanBulanan, HasilPrediksi
)

from .jenis_kendaraan_view import JenisKendaraanListView, JenisKendaraanDetailView
from .kecamatan_view import KecamatanListView, KecamatanDetailView
from .kelurahan_view import KelurahanListView, KelurahanDetailView
from .merek_kendaraan_view import MerekKendaraanListView, MerekKendaraanDetailView
from .type_kendaraan_view import TypeKendaraanListView, TypeKendaraanDetailView
from .wajib_pajak_view import WajibPajakListView, WajibPajakDetailView
from .kendaraan_bermotor_view import KendaraanBermotorListView, KendaraanBermotorDetailView
from .data_pajak_kendaraan_view import DataPajakKendaraanListView, DataPajakKendaraanDetailView
from .transaksi_pajak_view import (
    TransaksiPajakListView,
    TransaksiPajakDetailView,
    TransaksiPajakFilterOptionsView
)
from .agregat_pendapatan_bulanan_view import (
    AgregatPendapatanBulananListView,
    AgregatPendapatanBulananDetailView,
    AgregatPendapatanBulananRegenerateView,
    AgregatPendapatanBulananFilterOptionsView,
    AgregatPendapatanBulananSummaryView
)
from .hasil_prediksi_view import HasilPrediksiListView, HasilPrediksiDetailView
from .prediksi_view import (
    GeneratePrediksiView,
    ComparePrediksiView,
    PrediksiChartView,
    PrediksiEvaluationView,
    PrediksiTrendView
)
from .laporan_total_pajak_view import (
    LaporanTotalPajakView,
    LaporanTotalPajakSummaryView,
    LaporanTotalPajakFilterOptionsView
)


class DashboardView(APIView):
    """
    API endpoint untuk dashboard admin
    Menampilkan statistik dan data ringkasan sistem
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            # ============================================
            # STATISTIK USER
            # ============================================
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            inactive_users = User.objects.filter(is_active=False).count()
            
            users_by_role = User.objects.values('role').annotate(
                count=Count('id')
            ).order_by('role')
            
            role_statistics = {}
            for item in users_by_role:
                role_statistics[item['role']] = item['count']
            
            # ============================================
            # STATISTIK KENDARAAN BERMOTOR
            # ============================================
            total_kendaraan = KendaraanBermotor.objects.count()
            kendaraan_by_jenis = KendaraanBermotor.objects.values(
                'jenis__nama'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Kendaraan baru (30 hari terakhir)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            kendaraan_baru = KendaraanBermotor.objects.filter(
                created_at__gte=thirty_days_ago
            ).count()
            
            # ============================================
            # STATISTIK WAJIB PAJAK
            # ============================================
            total_wajib_pajak = WajibPajak.objects.count()
            wajib_pajak_by_kecamatan = WajibPajak.objects.values(
                'kelurahan__kecamatan__nama'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]  # Top 5
            
            # ============================================
            # STATISTIK TRANSAKSI PAJAK
            # ============================================
            total_transaksi = TransaksiPajak.objects.count()
            
            # Total pendapatan semua waktu
            total_pendapatan_all = TransaksiPajak.objects.aggregate(
                total=Sum('total_bayar')
            )['total'] or Decimal('0')
            
            # Pendapatan bulan ini
            current_month = timezone.now().month
            current_year = timezone.now().year
            pendapatan_bulan_ini = TransaksiPajak.objects.filter(
                tahun=current_year,
                bulan=current_month
            ).aggregate(
                total=Sum('total_bayar')
            )['total'] or Decimal('0')
            
            # Pendapatan bulan lalu
            last_month = current_month - 1 if current_month > 1 else 12
            last_year = current_year if current_month > 1 else current_year - 1
            pendapatan_bulan_lalu = TransaksiPajak.objects.filter(
                tahun=last_year,
                bulan=last_month
            ).aggregate(
                total=Sum('total_bayar')
            )['total'] or Decimal('0')
            
            # Transaksi bulan ini
            transaksi_bulan_ini = TransaksiPajak.objects.filter(
                tahun=current_year,
                bulan=current_month
            ).count()
            
            # Transaksi 7 hari terakhir
            seven_days_ago = timezone.now() - timedelta(days=7)
            transaksi_7_hari = TransaksiPajak.objects.filter(
                created_at__gte=seven_days_ago
            ).count()
            
            # ============================================
            # STATISTIK PENDAPATAN PER JENIS KENDARAAN
            # ============================================
            pendapatan_by_jenis = TransaksiPajak.objects.values(
                'kendaraan__jenis__nama'
            ).annotate(
                total=Sum('total_bayar'),
                count=Count('id')
            ).order_by('-total')[:5]  # Top 5
            
            # ============================================
            # STATISTIK AGREGAT PENDAPATAN
            # ============================================
            total_agregat = AgregatPendapatanBulanan.objects.count()
            agregat_bulan_ini = AgregatPendapatanBulanan.objects.filter(
                tahun=current_year,
                bulan=current_month
            ).aggregate(
                total=Sum('total_pendapatan')
            )['total'] or Decimal('0')
            
            # ============================================
            # STATISTIK PREDIKSI
            # ============================================
            total_prediksi = HasilPrediksi.objects.count()
            prediksi_by_metode = HasilPrediksi.objects.values(
                'metode'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Prediksi terbaru
            prediksi_terbaru = HasilPrediksi.objects.order_by(
                '-tahun_prediksi', '-bulan_prediksi'
            ).first()
            
            # ============================================
            # STATISTIK MASTER DATA
            # ============================================
            total_jenis_kendaraan = JenisKendaraan.objects.count()
            total_kecamatan = Kecamatan.objects.count()
            total_kelurahan = Kelurahan.objects.count()
            
            # ============================================
            # FORMAT DATA
            # ============================================
            dashboard_data = {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'inactive': inactive_users,
                    'by_role': role_statistics,
                },
                'kendaraan': {
                    'total': total_kendaraan,
                    'baru_30_hari': kendaraan_baru,
                    'by_jenis': [
                        {
                            'jenis': item['jenis__nama'],
                            'count': item['count']
                        }
                        for item in kendaraan_by_jenis
                    ],
                },
                'wajib_pajak': {
                    'total': total_wajib_pajak,
                    'by_kecamatan': [
                        {
                            'kecamatan': item['kelurahan__kecamatan__nama'],
                            'count': item['count']
                        }
                        for item in wajib_pajak_by_kecamatan
                    ],
                },
                'transaksi': {
                    'total': total_transaksi,
                    'bulan_ini': transaksi_bulan_ini,
                    '7_hari_terakhir': transaksi_7_hari,
                },
                'pendapatan': {
                    'total_all_time': float(total_pendapatan_all),
                    'bulan_ini': float(pendapatan_bulan_ini),
                    'bulan_lalu': float(pendapatan_bulan_lalu),
                    'selisih_bulan_ini': float(pendapatan_bulan_ini - pendapatan_bulan_lalu),
                    'persentase_perubahan': float(
                        ((pendapatan_bulan_ini - pendapatan_bulan_lalu) / pendapatan_bulan_lalu * 100)
                        if pendapatan_bulan_lalu > 0 else 0
                    ),
                    'by_jenis_kendaraan': [
                        {
                            'jenis': item['kendaraan__jenis__nama'],
                            'total': float(item['total']),
                            'count': item['count']
                        }
                        for item in pendapatan_by_jenis
                    ],
                },
                'agregat': {
                    'total': total_agregat,
                    'bulan_ini': float(agregat_bulan_ini),
                },
                'prediksi': {
                    'total': total_prediksi,
                    'by_metode': [
                        {
                            'metode': item['metode'],
                            'count': item['count']
                        }
                        for item in prediksi_by_metode
                    ],
                    'terbaru': {
                        'tahun': prediksi_terbaru.tahun_prediksi if prediksi_terbaru else None,
                        'bulan': prediksi_terbaru.bulan_prediksi if prediksi_terbaru else None,
                        'metode': prediksi_terbaru.metode if prediksi_terbaru else None,
                        'nilai': float(prediksi_terbaru.nilai_prediksi) if prediksi_terbaru else None,
                    } if prediksi_terbaru else None,
                },
                'master_data': {
                    'jenis_kendaraan': total_jenis_kendaraan,
                    'kecamatan': total_kecamatan,
                    'kelurahan': total_kelurahan,
                },
                'periode': {
                    'tahun_sekarang': current_year,
                    'bulan_sekarang': current_month,
                    'bulan_lalu': last_month,
                    'tahun_lalu': last_year,
                }
            }
            
            return APIResponse.success(
                data=dashboard_data,
                message='Data dashboard berhasil diambil',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            import traceback
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data dashboard',
                errors=str(e) + '\n' + traceback.format_exc(),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

