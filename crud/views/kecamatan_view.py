from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator

from crud.models import Kecamatan
from crud.serializers.kecamatan_serializer import KecamatanSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class KecamatanListView(APIView):
    """
    API endpoint untuk list dan create Kecamatan
    GET: List semua kecamatan (dengan pagination dan search)
    POST: Create kecamatan baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua kecamatan dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            
            # Query base
            queryset = Kecamatan.objects.all()
            
            # Filter by search (nama)
            if search:
                queryset = queryset.filter(nama__icontains=search)
            
            # Ordering
            queryset = queryset.order_by('nama')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = KecamatanSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data kecamatan berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data kecamatan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create kecamatan baru
        """
        try:
            serializer = KecamatanSerializer(data=request.data)
            
            if serializer.is_valid():
                kecamatan = serializer.save()
                return APIResponse.success(
                    data=KecamatanSerializer(kecamatan).data,
                    message='Kecamatan berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat kecamatan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KecamatanDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete Kecamatan
    GET: Get detail kecamatan
    PUT: Update kecamatan
    PATCH: Partial update kecamatan
    DELETE: Delete kecamatan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return Kecamatan.objects.get(pk=pk)
        except Kecamatan.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail kecamatan
        """
        try:
            kecamatan = self.get_object(pk)
            
            if not kecamatan:
                return APIResponse.error(
                    message='Kecamatan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KecamatanSerializer(kecamatan)
            return APIResponse.success(
                data=serializer.data,
                message='Data kecamatan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data kecamatan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap kecamatan
        """
        try:
            kecamatan = self.get_object(pk)
            
            if not kecamatan:
                return APIResponse.error(
                    message='Kecamatan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KecamatanSerializer(kecamatan, data=request.data)
            
            if serializer.is_valid():
                kecamatan = serializer.save()
                return APIResponse.success(
                    data=KecamatanSerializer(kecamatan).data,
                    message='Kecamatan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate kecamatan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update kecamatan
        """
        try:
            kecamatan = self.get_object(pk)
            
            if not kecamatan:
                return APIResponse.error(
                    message='Kecamatan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = KecamatanSerializer(kecamatan, data=request.data, partial=True)
            
            if serializer.is_valid():
                kecamatan = serializer.save()
                return APIResponse.success(
                    data=KecamatanSerializer(kecamatan).data,
                    message='Kecamatan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate kecamatan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete kecamatan
        """
        try:
            kecamatan = self.get_object(pk)
            
            if not kecamatan:
                return APIResponse.error(
                    message='Kecamatan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Cek apakah kecamatan digunakan oleh kelurahan
            from crud.models import Kelurahan
            kelurahan_count = Kelurahan.objects.filter(kecamatan=kecamatan).count()
            
            if kelurahan_count > 0:
                return APIResponse.error(
                    message=f'Kecamatan tidak dapat dihapus karena masih digunakan oleh {kelurahan_count} kelurahan',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            nama = kecamatan.nama
            kecamatan.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Kecamatan "{nama}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus kecamatan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

