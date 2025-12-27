from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from myauth.models import User
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .jenis_kendaraan_view import JenisKendaraanListView, JenisKendaraanDetailView
from .kecamatan_view import KecamatanListView, KecamatanDetailView
from .kelurahan_view import KelurahanListView, KelurahanDetailView
from .merek_kendaraan_view import MerekKendaraanListView, MerekKendaraanDetailView
from .type_kendaraan_view import TypeKendaraanListView, TypeKendaraanDetailView
from .wajib_pajak_view import WajibPajakListView, WajibPajakDetailView
from .kendaraan_bermotor_view import KendaraanBermotorListView, KendaraanBermotorDetailView
from .data_pajak_kendaraan_view import DataPajakKendaraanListView, DataPajakKendaraanDetailView
from .transaksi_pajak_view import TransaksiPajakListView, TransaksiPajakDetailView
from .agregat_pendapatan_bulanan_view import (
    AgregatPendapatanBulananListView,
    AgregatPendapatanBulananDetailView,
    AgregatPendapatanBulananRegenerateView
)
from .hasil_prediksi_view import HasilPrediksiListView, HasilPrediksiDetailView
from .prediksi_view import (
    GeneratePrediksiView,
    ComparePrediksiView,
    PrediksiChartView,
    PrediksiEvaluationView,
    PrediksiTrendView
)


class DashboardView(APIView):
    """
    API endpoint untuk dashboard admin
    Menampilkan statistik dan data ringkasan sistem
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            # Statistik User
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            inactive_users = User.objects.filter(is_active=False).count()
            
            # Statistik User berdasarkan Role
            users_by_role = User.objects.values('role').annotate(
                count=Count('id')
            ).order_by('role')
            
            # Statistik User berdasarkan Status
            staff_users = User.objects.filter(is_staff=True).count()
            superuser_count = User.objects.filter(is_superuser=True).count()
            
            # User baru (7 hari terakhir)
            seven_days_ago = timezone.now() - timedelta(days=7)
            new_users_week = User.objects.filter(date_joined__gte=seven_days_ago).count()
            
            # User baru (30 hari terakhir)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            new_users_month = User.objects.filter(date_joined__gte=thirty_days_ago).count()
            
            # Format data role
            role_statistics = {}
            for item in users_by_role:
                role_statistics[item['role']] = item['count']
            
            # Data dashboard
            dashboard_data = {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'inactive': inactive_users,
                    'staff': staff_users,
                    'superuser': superuser_count,
                    'by_role': role_statistics,
                    'new_users': {
                        'last_7_days': new_users_week,
                        'last_30_days': new_users_month,
                    }
                },
                'summary': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'inactive_users': inactive_users,
                }
            }
            
            return APIResponse.success(
                data=dashboard_data,
                message='Data dashboard berhasil diambil',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data dashboard',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

