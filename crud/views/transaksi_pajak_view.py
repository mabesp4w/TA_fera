from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime

from crud.models import TransaksiPajak
from crud.serializers.transaksi_pajak_serializer import TransaksiPajakSerializer
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin, IsAdminOrPimpinan


class TransaksiPajakListView(APIView):
    """
    API endpoint untuk list dan create TransaksiPajak
    GET: List semua transaksi pajak (dengan pagination dan search) - Admin & Pimpinan
    POST: Create transaksi pajak baru - Admin only
    """
    permission_classes = [IsAuthenticated, IsAdminOrPimpinan]
    
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
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')
            no_polisi = request.query_params.get('no_polisi', '')
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            
            # Query base dengan select_related untuk optimasi
            queryset = TransaksiPajak.objects.select_related(
                'kendaraan__type_kendaraan', 
                'kendaraan__type_kendaraan__merek',
                'kendaraan__jenis'
            ).all()
            
            # Filter by search (no_polisi kendaraan)
            if search:
                queryset = queryset.filter(
                    Q(kendaraan__no_polisi__icontains=search) |
                    Q(kendaraan__type_kendaraan__merek__nama__icontains=search) |
                    Q(kendaraan__type_kendaraan__nama__icontains=search)
                )
            
            # Filter by kendaraan_id
            if kendaraan_id:
                queryset = queryset.filter(kendaraan_id=kendaraan_id)
            
            # Filter by jenis_kendaraan_id
            if jenis_kendaraan_id:
                queryset = queryset.filter(kendaraan__jenis_id=jenis_kendaraan_id)
            
            # Filter by no_polisi
            if no_polisi:
                queryset = queryset.filter(kendaraan__no_polisi__icontains=no_polisi)
            
            # Filter by tahun (dengan konversi ke integer)
            if tahun:
                try:
                    tahun_int = int(tahun)
                    queryset = queryset.filter(tahun=tahun_int)
                except (ValueError, TypeError):
                    pass
            
            # Filter by bulan (dengan konversi ke integer)
            if bulan:
                try:
                    bulan_int = int(bulan)
                    queryset = queryset.filter(bulan=bulan_int)
                except (ValueError, TypeError):
                    pass
            
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
    GET: Get detail transaksi pajak - Admin & Pimpinan
    PUT/PATCH/DELETE: Modifikasi - Admin only
    """
    permission_classes = [IsAuthenticated, IsAdminOrPimpinan]
    
    def get_object(self, pk):
        """
        Helper method untuk get object atau raise 404
        """
        try:
            return TransaksiPajak.objects.select_related(
                'kendaraan__type_kendaraan', 
                'kendaraan__type_kendaraan__merek',
                'kendaraan__jenis'
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


class TransaksiPajakFilterOptionsView(APIView):
    """
    API endpoint untuk mendapatkan filter options (tahun dan bulan)
    GET: Get list tahun dan bulan yang tersedia di database - Admin & Pimpinan
    """
    permission_classes = [IsAuthenticated, IsAdminOrPimpinan]

    def get(self, request):
        """
        Get filter options untuk transaksi pajak
        """
        try:
            # Get unique tahun yang tersedia di database
            tahun_list = TransaksiPajak.objects.values_list('tahun', flat=True).distinct().order_by('-tahun')
            tahun_options = [{'value': t, 'label': str(t)} for t in tahun_list]

            # Get unique bulan yang tersedia di database
            bulan_list = TransaksiPajak.objects.values_list('bulan', flat=True).distinct().order_by('bulan')
            bulan_names = {
                1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
            }
            bulan_options = [{'value': b, 'label': bulan_names.get(b, str(b))} for b in bulan_list]

            return APIResponse.success(
                data={
                    'tahun_options': tahun_options,
                    'bulan_options': bulan_options
                },
                message='Filter options berhasil diambil'
            )

        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil filter options',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransaksiPajakBulkDeleteView(APIView):
    """
    API endpoint untuk menghapus multiple transaksi pajak berdasarkan filter
    DELETE: Delete transaksi pajak berdasarkan filter (tahun, bulan, jenis_kendaraan)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request):
        """
        Hapus transaksi pajak berdasarkan filter
        Query parameters:
        - tahun: Filter tahun pajak (WAJIB)
        - bulan: Filter bulan pajak
        - jenis_kendaraan_id: Filter jenis kendaraan
        Minimal: tahun + bulan, atau tahun + jenis_kendaraan_id
        """
        try:
            # Get query parameters
            tahun = request.query_params.get('tahun', '')
            bulan = request.query_params.get('bulan', '')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id', '')

            # Validasi: tahun WAJIB terisi
            if not tahun:
                return APIResponse.error(
                    message='Filter tahun wajib diisi',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validasi: minimal tahun + bulan atau tahun + jenis_kendaraan_id
            if not bulan and not jenis_kendaraan_id:
                return APIResponse.error(
                    message='Minimal filter bulan atau jenis kendaraan harus diisi bersamaan dengan tahun',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Build queryset dengan filter
            queryset = TransaksiPajak.objects.all()

            # Filter by tahun
            if tahun:
                try:
                    tahun_int = int(tahun)
                    queryset = queryset.filter(tahun=tahun_int)
                except (ValueError, TypeError):
                    return APIResponse.error(
                        message='Filter tahun tidak valid',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            # Filter by bulan
            if bulan:
                try:
                    bulan_int = int(bulan)
                    queryset = queryset.filter(bulan=bulan_int)
                except (ValueError, TypeError):
                    return APIResponse.error(
                        message='Filter bulan tidak valid',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            # Filter by jenis_kendaraan_id
            if jenis_kendaraan_id:
                try:
                    jenis_id_int = int(jenis_kendaraan_id)
                    queryset = queryset.filter(kendaraan__jenis_id=jenis_id_int)
                except (ValueError, TypeError):
                    return APIResponse.error(
                        message='Filter jenis kendaraan tidak valid',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            # Hitung jumlah data yang akan dihapus
            count = queryset.count()

            if count == 0:
                return APIResponse.error(
                    message='Tidak ada data transaksi yang sesuai dengan filter',
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Hapus semua data yang sesuai filter
            deleted_count, _ = queryset.delete()

            # Buat deskripsi filter untuk pesan response
            filter_desc = []
            if tahun:
                filter_desc.append(f'tahun {tahun}')
            if bulan:
                bulan_names = {
                    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
                }
                filter_desc.append(f'bulan {bulan_names.get(int(bulan), bulan)}')
            if jenis_kendaraan_id:
                filter_desc.append(f'jenis kendaraan ID {jenis_kendaraan_id}')

            filter_str = ', '.join(filter_desc)

            return APIResponse.success(
                data={
                    'deleted_count': deleted_count
                },
                message=f'Berhasil menghapus {deleted_count} transaksi pajak dengan filter {filter_str}',
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat menghapus transaksi pajak',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

