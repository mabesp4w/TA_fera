from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime

from crud.models import TransaksiPajak
from crud.serializers.transaksi_pajak_serializer import TransaksiPajakSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class TransaksiPajakListView(APIView):
    """
    API endpoint untuk list dan create TransaksiPajak
    GET: List semua transaksi pajak (dengan pagination dan search)
    POST: Create transaksi pajak baru
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get list semua transaksi pajak dengan pagination dan search
        """
        try:
            # Get query parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            search = request.query_params.get('search', '')
            kendaraan_id = request.query_params.get('kendaraan_id', '')
            no_polisi = request.query_params.get('no_polisi', '')
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            
            # Query base dengan select_related untuk optimasi
            queryset = TransaksiPajak.objects.select_related(
                'kendaraan__merek', 'kendaraan__type_kendaraan'
            ).all()
            
            # Filter by search (no_polisi kendaraan)
            if search:
                queryset = queryset.filter(
                    Q(kendaraan__no_polisi__icontains=search) |
                    Q(kendaraan__merek__nama__icontains=search) |
                    Q(kendaraan__type_kendaraan__nama__icontains=search)
                )
            
            # Filter by kendaraan_id
            if kendaraan_id:
                queryset = queryset.filter(kendaraan_id=kendaraan_id)
            
            # Filter by no_polisi
            if no_polisi:
                queryset = queryset.filter(kendaraan__no_polisi__icontains=no_polisi)
            
            # Filter by tahun
            if tahun:
                queryset = queryset.filter(tahun=tahun)
            
            # Filter by bulan
            if bulan:
                queryset = queryset.filter(bulan=bulan)
            
            # Ordering
            queryset = queryset.order_by('-tahun', '-bulan', '-created_at')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            serializer = TransaksiPajakSerializer(page_obj, many=True)
            
            # Response dengan pagination info
            return APIResponse.paginated_success(
                data=serializer.data,
                message='Data transaksi pajak berhasil diambil',
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
                message='Terjadi kesalahan saat mengambil data transaksi pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create transaksi pajak baru
        """
        try:
            serializer = TransaksiPajakSerializer(data=request.data)
            
            if serializer.is_valid():
                transaksi = serializer.save()
                return APIResponse.success(
                    data=TransaksiPajakSerializer(transaksi).data,
                    message='Transaksi pajak berhasil dibuat',
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
                message='Terjadi kesalahan saat membuat transaksi pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransaksiPajakDetailView(APIView):
    """
    API endpoint untuk detail, update, dan delete TransaksiPajak
    GET: Get detail transaksi pajak
    PUT: Update transaksi pajak
    PATCH: Partial update transaksi pajak
    DELETE: Delete transaksi pajak
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return TransaksiPajak.objects.select_related(
                'kendaraan__merek', 'kendaraan__type_kendaraan'
            ).get(pk=pk)
        except TransaksiPajak.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """
        Get detail transaksi pajak
        """
        try:
            transaksi = self.get_object(pk)
            
            if not transaksi:
                return APIResponse.error(
                    message='Transaksi pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = TransaksiPajakSerializer(transaksi)
            return APIResponse.success(
                data=serializer.data,
                message='Data transaksi pajak berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data transaksi pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        """
        Update lengkap transaksi pajak
        """
        try:
            transaksi = self.get_object(pk)
            
            if not transaksi:
                return APIResponse.error(
                    message='Transaksi pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = TransaksiPajakSerializer(transaksi, data=request.data)
            
            if serializer.is_valid():
                transaksi = serializer.save()
                return APIResponse.success(
                    data=TransaksiPajakSerializer(transaksi).data,
                    message='Transaksi pajak berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate transaksi pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk):
        """
        Partial update transaksi pajak
        """
        try:
            transaksi = self.get_object(pk)
            
            if not transaksi:
                return APIResponse.error(
                    message='Transaksi pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            serializer = TransaksiPajakSerializer(transaksi, data=request.data, partial=True)
            
            if serializer.is_valid():
                transaksi = serializer.save()
                return APIResponse.success(
                    data=TransaksiPajakSerializer(transaksi).data,
                    message='Transaksi pajak berhasil diupdate'
                )
            else:
                return APIResponse.error(
                    message='Data tidak valid',
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengupdate transaksi pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk):
        """
        Delete transaksi pajak
        """
        try:
            transaksi = self.get_object(pk)
            
            if not transaksi:
                return APIResponse.error(
                    message='Transaksi pajak tidak ditemukan',
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            no_polisi = transaksi.kendaraan.no_polisi
            periode = f"{transaksi.tahun}-{transaksi.bulan:02d}"
            transaksi.delete()
            
            return APIResponse.success(
                data=None,
                message=f'Transaksi pajak untuk "{no_polisi}" periode {periode} berhasil dihapus',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus transaksi pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

