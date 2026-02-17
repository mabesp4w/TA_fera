from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator

from crud.models import TypeKendaraan
from crud.serializers.type_kendaraan_serializer import TypeKendaraanSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class TypeKendaraanListView(APIView):
    """
    API endpoint untuk list dan create TypeKendaraan
    GET: List semua type kendaraan (dengan pagination dan search)
    POST: Create type kendaraan baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua type kendaraan dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            merek_id = request.query_params.get('merek_id', '')
            
            # Query base
            queryset = TypeKendaraan.objects.select_related('merek').all()
            
            # Filter by search (nama)
            if search:
                queryset = queryset.filter(nama__icontains=search)
            
            # Filter by merek
            if merek_id:
                queryset = queryset.filter(merek_id=merek_id)
            
            # Ordering
            queryset = queryset.order_by('merek__nama', 'nama')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = TypeKendaraanSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data type kendaraan berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data type kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create type kendaraan baru
        """
        try:
            serializer = TypeKendaraanSerializer(data=request.data)
            
            if serializer.is_valid():
                type_kendaraan = serializer.save()
                return APIResponse.success(
                    data=TypeKendaraanSerializer(type_kendaraan).data,
                    message='Type kendaraan berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat type kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TypeKendaraanDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete TypeKendaraan
    GET: Get detail type kendaraan
    PUT: Update type kendaraan
    PATCH: Partial update type kendaraan
    DELETE: Delete type kendaraan
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return TypeKendaraan.objects.select_related('merek').get(pk=pk)
        except TypeKendaraan.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail type kendaraan
        """
        try:
            type_kendaraan = self.get_object(pk)
            
            if not type_kendaraan:
                return APIResponse.error(
                    message='Type kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = TypeKendaraanSerializer(type_kendaraan)
            return APIResponse.success(
                data=serializer.data,
                message='Data type kendaraan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data type kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap type kendaraan
        """
        try:
            type_kendaraan = self.get_object(pk)
            
            if not type_kendaraan:
                return APIResponse.error(
                    message='Type kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = TypeKendaraanSerializer(type_kendaraan, data=request.data)
            
            if serializer.is_valid():
                type_kendaraan = serializer.save()
                return APIResponse.success(
                    data=TypeKendaraanSerializer(type_kendaraan).data,
                    message='Type kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate type kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update type kendaraan
        """
        try:
            type_kendaraan = self.get_object(pk)
            
            if not type_kendaraan:
                return APIResponse.error(
                    message='Type kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = TypeKendaraanSerializer(type_kendaraan, data=request.data, partial=True)
            
            if serializer.is_valid():
                type_kendaraan = serializer.save()
                return APIResponse.success(
                    data=TypeKendaraanSerializer(type_kendaraan).data,
                    message='Type kendaraan berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate type kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete type kendaraan
        """
        try:
            type_kendaraan = self.get_object(pk)
            
            if not type_kendaraan:
                return APIResponse.error(
                    message='Type kendaraan tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Cek apakah type kendaraan digunakan oleh kendaraan
            from crud.models import KendaraanBermotor
            kendaraan_count = KendaraanBermotor.objects.filter(type_kendaraan=type_kendaraan).count()
            
            if kendaraan_count > 0:
                return APIResponse.error(
                    message=f'Type kendaraan tidak dapat dihapus karena masih digunakan oleh {kendaraan_count} kendaraan',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            nama = type_kendaraan.nama
            merek_nama = type_kendaraan.merek.nama
            type_kendaraan.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Type kendaraan "{merek_nama} - {nama}" berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus type kendaraan',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

