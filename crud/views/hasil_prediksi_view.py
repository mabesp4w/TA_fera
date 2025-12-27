from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q

from crud.models import HasilPrediksi
from crud.serializers.hasil_prediksi_serializer import HasilPrediksiSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class HasilPrediksiListView(APIView):
    """
    API endpoint untuk list dan create HasilPrediksi
    GET: List semua hasil prediksi (dengan pagination dan search)
    POST: Create hasil prediksi baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua hasil prediksi dengan pagination dan filter
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            tahun_prediksi = request.query_params.get('tahun_prediksi', '')
            bulan_prediksi = request.query_params.get('bulan_prediksi', '')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')
            metode = request.query_params.get('metode', '')
            
            # Query base dengan select_related untuk optimasi
            queryset = HasilPrediksi.objects.select_related('jenis_kendaraan').all()
            
            # Filter by tahun_prediksi
            if tahun_prediksi:
                queryset = queryset.filter(tahun_prediksi=tahun_prediksi)
            
            # Filter by bulan_prediksi
            if bulan_prediksi:
                queryset = queryset.filter(bulan_prediksi=bulan_prediksi)
            
            # Filter by jenis_kendaraan
            if jenis_kendaraan_id:
                queryset = queryset.filter(jenis_kendaraan_id=jenis_kendaraan_id)
            
            # Filter by metode
            if metode:
                queryset = queryset.filter(metode=metode)
            
            # Ordering
            queryset = queryset.order_by('-tahun_prediksi', '-bulan_prediksi', '-tanggal_prediksi')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = HasilPrediksiSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data hasil prediksi berhasil diambil',
                pagination_data={
                    'page': page_obj.number,
                    'page_size': int(page_size),
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data hasil prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create hasil prediksi baru
        """
        try:
            serializer = HasilPrediksiSerializer(data=request.data)
            
            if serializer.is_valid():
                hasil_prediksi = serializer.save()
                return APIResponse.success(
                    data=HasilPrediksiSerializer(hasil_prediksi).data,
                    message='Hasil prediksi berhasil dibuat',
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat membuat hasil prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HasilPrediksiDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete HasilPrediksi
    GET: Get detail hasil prediksi
    PUT: Update hasil prediksi
    PATCH: Partial update hasil prediksi (untuk update nilai_aktual)
    DELETE: Delete hasil prediksi
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return HasilPrediksi.objects.select_related('jenis_kendaraan').get(pk=pk)
        except HasilPrediksi.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail hasil prediksi
        """
        try:
            hasil_prediksi = self.get_object(pk)
            
            if not hasil_prediksi:
                return APIResponse.error(
                    message='Hasil prediksi tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = HasilPrediksiSerializer(hasil_prediksi)
            return APIResponse.success(
                data=serializer.data,
                message='Data hasil prediksi berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data hasil prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap hasil prediksi
        """
        try:
            hasil_prediksi = self.get_object(pk)
            
            if not hasil_prediksi:
                return APIResponse.error(
                    message='Hasil prediksi tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = HasilPrediksiSerializer(hasil_prediksi, data=request.data)
            
            if serializer.is_valid():
                hasil_prediksi = serializer.save()
                return APIResponse.success(
                    data=HasilPrediksiSerializer(hasil_prediksi).data,
                    message='Hasil prediksi berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate hasil prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update hasil prediksi
        Berguna untuk update nilai_aktual setelah periode prediksi selesai
        """
        try:
            hasil_prediksi = self.get_object(pk)
            
            if not hasil_prediksi:
                return APIResponse.error(
                    message='Hasil prediksi tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = HasilPrediksiSerializer(hasil_prediksi, data=request.data, partial=True)
            
            if serializer.is_valid():
                hasil_prediksi = serializer.save()
                return APIResponse.success(
                    data=HasilPrediksiSerializer(hasil_prediksi).data,
                    message='Hasil prediksi berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate hasil prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete hasil prediksi
        """
        try:
            hasil_prediksi = self.get_object(pk)
            
            if not hasil_prediksi:
                return APIResponse.error(
                    message='Hasil prediksi tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            metode = hasil_prediksi.get_metode_display()
            periode = f"{hasil_prediksi.tahun_prediksi}-{hasil_prediksi.bulan_prediksi:02d}"
            hasil_prediksi.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Hasil prediksi {metode} untuk periode {periode} berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus hasil prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

