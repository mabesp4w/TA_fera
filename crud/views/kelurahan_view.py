from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator

from crud.models import Kelurahan
from crud.serializers.kelurahan_serializer import KelurahanSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class KelurahanListView(APIView):
    """
    API endpoint untuk list dan create Kelurahan
    GET: List semua kelurahan (dengan pagination dan search)
    POST: Create kelurahan baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua kelurahan dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            kecamatan_id = request.query_params.get('kecamatan_id', '')
            
            # Query base
            queryset = Kelurahan.objects.select_related('kecamatan').all()
            
            # Filter by search (nama)
            if search:
                queryset = queryset.filter(nama__icontains=search)
            
            # Filter by kecamatan
            if kecamatan_id:
                queryset = queryset.filter(kecamatan_id=kecamatan_id)
            
            # Ordering
            queryset = queryset.order_by('kecamatan__nama', 'nama')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = KelurahanSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data kelurahan berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data kelurahan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create kelurahan baru
        """
        try:
            serializer = KelurahanSerializer(data=request.data)
            
            if serializer.is_valid():
                kelurahan = serializer.save()
                return APIResponse.success(
                    data=KelurahanSerializer(kelurahan).data,
                    message='Kelurahan berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat kelurahan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KelurahanDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete Kelurahan
    GET: Get detail kelurahan
    PUT: Update kelurahan
    PATCH: Partial update kelurahan
    DELETE: Delete kelurahan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return Kelurahan.objects.select_related('kecamatan').get(pk=pk)
        except Kelurahan.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail kelurahan
        """
        try:
            kelurahan = self.get_object(pk)
            
            if not kelurahan:
                return APIResponse.error(
                    message='Kelurahan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KelurahanSerializer(kelurahan)
            return APIResponse.success(
                data=serializer.data,
                message='Data kelurahan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data kelurahan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap kelurahan
        """
        try:
            kelurahan = self.get_object(pk)
            
            if not kelurahan:
                return APIResponse.error(
                    message='Kelurahan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KelurahanSerializer(kelurahan, data=request.data)
            
            if serializer.is_valid():
                kelurahan = serializer.save()
                return APIResponse.success(
                    data=KelurahanSerializer(kelurahan).data,
                    message='Kelurahan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate kelurahan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update kelurahan
        """
        try:
            kelurahan = self.get_object(pk)
            
            if not kelurahan:
                return APIResponse.error(
                    message='Kelurahan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KelurahanSerializer(kelurahan, data=request.data, partial=True)
            
            if serializer.is_valid():
                kelurahan = serializer.save()
                return APIResponse.success(
                    data=KelurahanSerializer(kelurahan).data,
                    message='Kelurahan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate kelurahan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete kelurahan
        """
        try:
            kelurahan = self.get_object(pk)
            
            if not kelurahan:
                return APIResponse.error(
                    message='Kelurahan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Cek apakah kelurahan digunakan oleh wajib pajak
            from crud.models import WajibPajak
            wajib_pajak_count = WajibPajak.objects.filter(kelurahan=kelurahan).count()
            
            if wajib_pajak_count > 0:
                return APIResponse.error(
                    message=f'Kelurahan tidak dapat dihapus karena masih digunakan oleh {wajib_pajak_count} wajib pajak',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            nama = kelurahan.nama
            kecamatan_nama = kelurahan.kecamatan.nama
            kelurahan.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Kelurahan "{nama}, {kecamatan_nama}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus kelurahan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

