from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q

from crud.models import JenisKendaraan
from crud.serializers.jenis_kendaraan_serializer import JenisKendaraanSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class JenisKendaraanListView(APIView):
    """
    API endpoint untuk list dan create JenisKendaraan
    GET: List semua jenis kendaraan (dengan pagination dan search)
    POST: Create jenis kendaraan baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua jenis kendaraan dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            kategori = request.query_params.get('kategori', '')
            
            # Query base
            queryset = JenisKendaraan.objects.all()
            
            # Filter by search (nama)
            if search:
                queryset = queryset.filter(nama__icontains=search)
            
            # Filter by kategori
            if kategori:
                queryset = queryset.filter(kategori=kategori)
            
            # Ordering
            queryset = queryset.order_by('nama')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = JenisKendaraanSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data jenis kendaraan berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data jenis kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create jenis kendaraan baru
        """
        try:
            serializer = JenisKendaraanSerializer(data=request.data)
            
            if serializer.is_valid():
                jenis_kendaraan = serializer.save()
                return APIResponse.success(
                    data=JenisKendaraanSerializer(jenis_kendaraan).data,
                    message='Jenis kendaraan berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat jenis kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JenisKendaraanDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete JenisKendaraan
    GET: Get detail jenis kendaraan
    PUT: Update jenis kendaraan
    PATCH: Partial update jenis kendaraan
    DELETE: Delete jenis kendaraan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return JenisKendaraan.objects.get(pk=pk)
        except JenisKendaraan.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail jenis kendaraan
        """
        try:
            jenis_kendaraan = self.get_object(pk)
            
            if not jenis_kendaraan:
                return APIResponse.error(
                    message='Jenis kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = JenisKendaraanSerializer(jenis_kendaraan)
            return APIResponse.success(
                data=serializer.data,
                message='Data jenis kendaraan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data jenis kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap jenis kendaraan
        """
        try:
            jenis_kendaraan = self.get_object(pk)
            
            if not jenis_kendaraan:
                return APIResponse.error(
                    message='Jenis kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = JenisKendaraanSerializer(jenis_kendaraan, data=request.data)
            
            if serializer.is_valid():
                jenis_kendaraan = serializer.save()
                return APIResponse.success(
                    data=JenisKendaraanSerializer(jenis_kendaraan).data,
                    message='Jenis kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate jenis kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update jenis kendaraan
        """
        try:
            jenis_kendaraan = self.get_object(pk)
            
            if not jenis_kendaraan:
                return APIResponse.error(
                    message='Jenis kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = JenisKendaraanSerializer(jenis_kendaraan, data=request.data, partial=True)
            
            if serializer.is_valid():
                jenis_kendaraan = serializer.save()
                return APIResponse.success(
                    data=JenisKendaraanSerializer(jenis_kendaraan).data,
                    message='Jenis kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate jenis kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete jenis kendaraan
        """
        try:
            jenis_kendaraan = self.get_object(pk)
            
            if not jenis_kendaraan:
                return APIResponse.error(
                    message='Jenis kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Cek apakah jenis kendaraan digunakan oleh kendaraan
            from crud.models import KendaraanBermotor
            kendaraan_count = KendaraanBermotor.objects.filter(jenis=jenis_kendaraan).count()
            
            if kendaraan_count > 0:
                return APIResponse.error(
                    message=f'Jenis kendaraan tidak dapat dihapus karena masih digunakan oleh {kendaraan_count} kendaraan',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            nama = jenis_kendaraan.nama
            jenis_kendaraan.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Jenis kendaraan "{nama}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus jenis kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

