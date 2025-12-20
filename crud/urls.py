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
]