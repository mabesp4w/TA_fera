from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardView,
    JenisKendaraanListView,
    JenisKendaraanDetailView,
    KecamatanListView,
    KecamatanDetailView,
    KelurahanListView,
    KelurahanDetailView,
    MerekKendaraanListView,
    MerekKendaraanDetailView,
    TypeKendaraanListView,
    TypeKendaraanDetailView,
    WajibPajakListView,
    WajibPajakDetailView,
    KendaraanBermotorListView,
    KendaraanBermotorDetailView,
    DataPajakKendaraanListView,
    DataPajakKendaraanDetailView,
    TransaksiPajakListView,
    TransaksiPajakDetailView,
    TransaksiPajakFilterOptionsView,
    AgregatPendapatanBulananListView,
    AgregatPendapatanBulananDetailView,
    AgregatPendapatanBulananRegenerateView,
    AgregatPendapatanBulananFilterOptionsView,
    AgregatPendapatanBulananSummaryView,
    HasilPrediksiListView,
    HasilPrediksiDetailView,
    GeneratePrediksiView,
    ComparePrediksiView,
    PrediksiChartView,
    PrediksiEvaluationView,
    PrediksiTrendView,
    LaporanTotalPajakView,
    LaporanTotalPajakSummaryView,
    LaporanTotalPajakFilterOptionsView,
)

router = DefaultRouter()

app_name = 'crud'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Jenis Kendaraan CRUD
    path('jenis-kendaraan/', JenisKendaraanListView.as_view(), name='jenis-kendaraan-list'),
    path('jenis-kendaraan/<int:pk>/', JenisKendaraanDetailView.as_view(), name='jenis-kendaraan-detail'),
    
    # Kecamatan CRUD
    path('kecamatan/', KecamatanListView.as_view(), name='kecamatan-list'),
    path('kecamatan/<int:pk>/', KecamatanDetailView.as_view(), name='kecamatan-detail'),
    
    # Kelurahan CRUD
    path('kelurahan/', KelurahanListView.as_view(), name='kelurahan-list'),
    path('kelurahan/<int:pk>/', KelurahanDetailView.as_view(), name='kelurahan-detail'),
    
    # Merek Kendaraan CRUD
    path('merek-kendaraan/', MerekKendaraanListView.as_view(), name='merek-kendaraan-list'),
    path('merek-kendaraan/<int:pk>/', MerekKendaraanDetailView.as_view(), name='merek-kendaraan-detail'),
    
    # Type Kendaraan CRUD
    path('type-kendaraan/', TypeKendaraanListView.as_view(), name='type-kendaraan-list'),
    path('type-kendaraan/<int:pk>/', TypeKendaraanDetailView.as_view(), name='type-kendaraan-detail'),
    
    # Wajib Pajak CRUD
    path('wajib-pajak/', WajibPajakListView.as_view(), name='wajib-pajak-list'),
    path('wajib-pajak/<int:pk>/', WajibPajakDetailView.as_view(), name='wajib-pajak-detail'),
    
    # Kendaraan Bermotor CRUD
    path('kendaraan-bermotor/', KendaraanBermotorListView.as_view(), name='kendaraan-bermotor-list'),
    path('kendaraan-bermotor/<int:pk>/', KendaraanBermotorDetailView.as_view(), name='kendaraan-bermotor-detail'),
    
    # Data Pajak Kendaraan CRUD
    path('data-pajak-kendaraan/', DataPajakKendaraanListView.as_view(), name='data-pajak-kendaraan-list'),
    path('data-pajak-kendaraan/<int:pk>/', DataPajakKendaraanDetailView.as_view(), name='data-pajak-kendaraan-detail'),
    
    # Transaksi Pajak CRUD
    path('transaksi-pajak/', TransaksiPajakListView.as_view(), name='transaksi-pajak-list'),
    path('transaksi-pajak/<int:pk>/', TransaksiPajakDetailView.as_view(), name='transaksi-pajak-detail'),
    path('transaksi-pajak/filter-options/', TransaksiPajakFilterOptionsView.as_view(), name='transaksi-pajak-filter-options'),
    
    # Agregat Pendapatan Bulanan (Read-only + Regenerate)
    path('agregat-pendapatan-bulanan/', AgregatPendapatanBulananListView.as_view(), name='agregat-pendapatan-bulanan-list'),
    path('agregat-pendapatan-bulanan/<int:pk>/', AgregatPendapatanBulananDetailView.as_view(), name='agregat-pendapatan-bulanan-detail'),
    path('agregat-pendapatan-bulanan/regenerate/', AgregatPendapatanBulananRegenerateView.as_view(), name='agregat-pendapatan-bulanan-regenerate'),
    path('agregat-pendapatan-bulanan/filter-options/', AgregatPendapatanBulananFilterOptionsView.as_view(), name='agregat-pendapatan-bulanan-filter-options'),
    path('agregat-pendapatan-bulanan/summary/', AgregatPendapatanBulananSummaryView.as_view(), name='agregat-pendapatan-bulanan-summary'),
    
    # Hasil Prediksi CRUD
    path('hasil-prediksi/', HasilPrediksiListView.as_view(), name='hasil-prediksi-list'),
    path('hasil-prediksi/<int:pk>/', HasilPrediksiDetailView.as_view(), name='hasil-prediksi-detail'),
    
    # Prediksi Endpoints
    path('prediksi/generate/', GeneratePrediksiView.as_view(), name='prediksi-generate'),
    path('prediksi/compare/', ComparePrediksiView.as_view(), name='prediksi-compare'),
    path('prediksi/chart/', PrediksiChartView.as_view(), name='prediksi-chart'),
    path('prediksi/evaluation/', PrediksiEvaluationView.as_view(), name='prediksi-evaluation'),
    path('prediksi/trend/', PrediksiTrendView.as_view(), name='prediksi-trend'),
    
    # Laporan Total Pajak
    path('laporan-total-pajak/', LaporanTotalPajakView.as_view(), name='laporan-total-pajak'),
    path('laporan-total-pajak/summary/', LaporanTotalPajakSummaryView.as_view(), name='laporan-total-pajak-summary'),
    path('laporan-total-pajak/filter-options/', LaporanTotalPajakFilterOptionsView.as_view(), name='laporan-total-pajak-filter-options'),
    ]