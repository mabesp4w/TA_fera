from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q

from crud.models import WajibPajak
from crud.serializers.wajib_pajak_serializer import WajibPajakSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class WajibPajakListView(APIView):
    """
    API endpoint untuk list dan create WajibPajak
    GET: List semua wajib pajak (dengan pagination dan search)
    POST: Create wajib pajak baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua wajib pajak dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            kelurahan_id = request.query_params.get('kelurahan_id', '')
            no_ktp = request.query_params.get('no_ktp', '')
            
            # Query base dengan select_related untuk optimasi
            queryset = WajibPajak.objects.select_related('kelurahan__kecamatan').all()
            
            # Filter by search (nama atau alamat)
            if search:
                queryset = queryset.filter(
                    Q(nama__icontains=search) | 
                    Q(alamat__icontains=search) |
                    Q(no_ktp__icontains=search)
                )
            
            # Filter by kelurahan
            if kelurahan_id:
                queryset = queryset.filter(kelurahan_id=kelurahan_id)
            
            # Filter by no_ktp
            if no_ktp:
                queryset = queryset.filter(no_ktp__icontains=no_ktp)
            
            # Ordering
            queryset = queryset.order_by('-created_at', 'nama')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = WajibPajakSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data wajib pajak berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data wajib pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create wajib pajak baru
        """
        try:
            serializer = WajibPajakSerializer(data=request.data)
            
            if serializer.is_valid():
                wajib_pajak = serializer.save()
                return APIResponse.success(
                    data=WajibPajakSerializer(wajib_pajak).data,
                    message='Wajib pajak berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat wajib pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WajibPajakDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete WajibPajak
    GET: Get detail wajib pajak
    PUT: Update wajib pajak
    PATCH: Partial update wajib pajak
    DELETE: Delete wajib pajak
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return WajibPajak.objects.select_related('kelurahan__kecamatan').get(pk=pk)
        except WajibPajak.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail wajib pajak
        """
        try:
            wajib_pajak = self.get_object(pk)
            
            if not wajib_pajak:
                return APIResponse.error(
                    message='Wajib pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = WajibPajakSerializer(wajib_pajak)
            return APIResponse.success(
                data=serializer.data,
                message='Data wajib pajak berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data wajib pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap wajib pajak
        """
        try:
            wajib_pajak = self.get_object(pk)
            
            if not wajib_pajak:
                return APIResponse.error(
                    message='Wajib pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = WajibPajakSerializer(wajib_pajak, data=request.data)
            
            if serializer.is_valid():
                wajib_pajak = serializer.save()
                return APIResponse.success(
                    data=WajibPajakSerializer(wajib_pajak).data,
                    message='Wajib pajak berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate wajib pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update wajib pajak
        """
        try:
            wajib_pajak = self.get_object(pk)
            
            if not wajib_pajak:
                return APIResponse.error(
                    message='Wajib pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = WajibPajakSerializer(wajib_pajak, data=request.data, partial=True)
            
            if serializer.is_valid():
                wajib_pajak = serializer.save()
                return APIResponse.success(
                    data=WajibPajakSerializer(wajib_pajak).data,
                    message='Wajib pajak berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate wajib pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete wajib pajak
        """
        try:
            wajib_pajak = self.get_object(pk)
            
            if not wajib_pajak:
                return APIResponse.error(
                    message='Wajib pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Cek apakah wajib pajak digunakan oleh kendaraan
            from crud.models import KendaraanBermotor
            kendaraan_count = KendaraanBermotor.objects.filter(wajib_pajak=wajib_pajak).count()
            
            if kendaraan_count > 0:
                return APIResponse.error(
                    message=f'Wajib pajak tidak dapat dihapus karena masih memiliki {kendaraan_count} kendaraan',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            nama = wajib_pajak.nama
            wajib_pajak.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Wajib pajak "{nama}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus wajib pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

