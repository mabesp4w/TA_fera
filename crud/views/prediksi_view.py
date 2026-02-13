from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from crud.models import HasilPrediksi, AgregatPendapatanBulanan, JenisKendaraan
from crud.serializers.hasil_prediksi_serializer import HasilPrediksiSerializer
from crud.services.prediction_service import PredictionService
from crud.services.hybrid_prediction_service import HybridPredictionService
from crud.utils.response import APIResponse
from crud.utils.permissions import IsAdmin


class GeneratePrediksiView(APIView):
    """
    API endpoint untuk generate prediksi menggunakan Exponential Smoothing
    POST: Generate prediksi baru dan simpan ke database
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request):
        """
        Generate prediksi baru
        
        Body:
        {
            "metode": "SES" | "DES" | "TES",
            "jenis_kendaraan_id": int (optional),
            "tahun_prediksi": int,
            "bulan_prediksi": int,
            "alpha": float (optional),
            "beta": float (optional),
            "gamma": float (optional),
            "seasonal_periods": int (optional, default: 12),
            "optimize": bool (optional, default: true),
            "keterangan": string (optional)
        }
        """
        try:
            metode = request.data.get('metode', 'SES').upper()
            jenis_kendaraan_id = request.data.get('jenis_kendaraan_id')
            tahun_prediksi = request.data.get('tahun_prediksi')
            bulan_prediksi = request.data.get('bulan_prediksi')
            alpha = request.data.get('alpha')
            beta = request.data.get('beta')
            gamma = request.data.get('gamma')
            seasonal_periods = request.data.get('seasonal_periods', 12)
            optimize = request.data.get('optimize', True)
            keterangan = request.data.get('keterangan', '')
            
            # Validasi
            if not tahun_prediksi or not bulan_prediksi:
                return APIResponse.error(
                    message='Tahun dan bulan prediksi harus diisi',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if metode not in ['SES', 'DES', 'TES']:
                return APIResponse.error(
                    message='Metode harus salah satu dari: SES, DES, TES',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert jenis_kendaraan_id
            jenis_kendaraan = None
            if jenis_kendaraan_id:
                try:
                    jenis_kendaraan = JenisKendaraan.objects.get(pk=jenis_kendaraan_id)
                except JenisKendaraan.DoesNotExist:
                    return APIResponse.error(
                        message='Jenis kendaraan tidak ditemukan',
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            
            # Generate prediction
            if metode == 'SES':
                result = PredictionService.predict_ses(
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    tahun_prediksi=tahun_prediksi,
                    bulan_prediksi=bulan_prediksi,
                    alpha=float(alpha) if alpha else None,
                    optimize=optimize
                )
            elif metode == 'DES':
                result = PredictionService.predict_des(
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    tahun_prediksi=tahun_prediksi,
                    bulan_prediksi=bulan_prediksi,
                    alpha=float(alpha) if alpha else None,
                    beta=float(beta) if beta else None,
                    optimize=optimize
                )
            else:  # TES
                result = PredictionService.predict_tes(
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    tahun_prediksi=tahun_prediksi,
                    bulan_prediksi=bulan_prediksi,
                    seasonal_periods=seasonal_periods,
                    alpha=float(alpha) if alpha else None,
                    beta=float(beta) if beta else None,
                    gamma=float(gamma) if gamma else None,
                    optimize=optimize
                )
            
            # Get actual value jika sudah ada
            actual_value = PredictionService.get_actual_value(
                tahun_prediksi, bulan_prediksi, jenis_kendaraan_id
            )
            
            if actual_value:
                result['nilai_aktual'] = actual_value
                result['error_absolut'] = abs(result['nilai_prediksi'] - actual_value)
                result['error_persentase'] = (result['error_absolut'] / actual_value * 100) if actual_value > 0 else 0
                result['akurasi'] = 100 - result['error_persentase']
            
            # Save to database
            hasil_prediksi = HasilPrediksi.objects.create(
                jenis_kendaraan=jenis_kendaraan,
                tahun_prediksi=tahun_prediksi,
                bulan_prediksi=bulan_prediksi,
                metode=metode,
                nilai_prediksi=result['nilai_prediksi'],
                alpha=result.get('alpha', 0),
                beta=result.get('beta', 0),
                gamma=result.get('gamma', 0),
                seasonal_periods=result.get('seasonal_periods', 12),
                mape=result.get('mape'),
                mae=result.get('mae'),
                rmse=result.get('rmse'),
                nilai_aktual=actual_value,
                data_training_dari=result.get('data_training_dari'),
                data_training_sampai=result.get('data_training_sampai'),
                jumlah_data_training=result.get('jumlah_data_training'),
                keterangan=keterangan or result.get('keterangan', '')
            )
            
            result['id'] = hasil_prediksi.id
            result['created_at'] = hasil_prediksi.created_at
            
            return APIResponse.success(
                data=result,
                message=f'Prediksi {metode} berhasil dibuat',
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat generate prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComparePrediksiView(APIView):
    """
    API endpoint untuk membandingkan semua metode prediksi
    GET: Membandingkan SES, DES, dan TES
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Membandingkan semua metode prediksi
        
        Query params:
        - tahun_prediksi: int (required)
        - bulan_prediksi: int (required)
        - jenis_kendaraan_id: int (optional)
        - seasonal_periods: int (optional, default: 12)
        """
        try:
            tahun_prediksi = request.query_params.get('tahun_prediksi')
            bulan_prediksi = request.query_params.get('bulan_prediksi')
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id')
            seasonal_periods = int(request.query_params.get('seasonal_periods', 12))
            
            # Validasi
            if not tahun_prediksi or not bulan_prediksi:
                return APIResponse.error(
                    message='Tahun dan bulan prediksi harus diisi',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate prediksi untuk setiap metode
            results = {}
            
            # SES
            try:
                result_ses = PredictionService.predict_ses(
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    tahun_prediksi=int(tahun_prediksi),
                    bulan_prediksi=int(bulan_prediksi),
                    optimize=True
                )
                results['SES'] = result_ses
            except Exception as e:
                results['SES'] = {'error': str(e)}
            
            # DES
            try:
                result_des = PredictionService.predict_des(
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    tahun_prediksi=int(tahun_prediksi),
                    bulan_prediksi=int(bulan_prediksi),
                    optimize=True
                )
                results['DES'] = result_des
            except Exception as e:
                results['DES'] = {'error': str(e)}
            
            # TES
            try:
                result_tes = PredictionService.predict_tes(
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    tahun_prediksi=int(tahun_prediksi),
                    bulan_prediksi=int(bulan_prediksi),
                    seasonal_periods=seasonal_periods,
                    optimize=True
                )
                results['TES'] = result_tes
            except Exception as e:
                results['TES'] = {'error': str(e)}
            
            # Hybrid
            try:
                result_hybrid = HybridPredictionService.predict_hybrid(
                    tahun_prediksi=int(tahun_prediksi),
                    bulan_prediksi=int(bulan_prediksi),
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    training_periods=24,
                    selected_scenario='base',
                    return_details=True
                )
                results['HYBRID'] = result_hybrid
            except Exception as e:
                results['HYBRID'] = {'error': str(e)}
            
            # Get actual value
            actual_value = PredictionService.get_actual_value(
                int(tahun_prediksi), int(bulan_prediksi), jenis_kendaraan_id
            )
            
            if actual_value:
                for key in results:
                    if 'error' not in results[key]:
                        prediksi = results[key]['nilai_prediksi']
                        results[key]['error_absolut'] = abs(prediksi - actual_value)
                        results[key]['error_persentase'] = (results[key]['error_absolut'] / actual_value * 100) if actual_value > 0 else 0
                        results[key]['akurasi'] = 100 - results[key]['error_persentase']
                        results[key]['nilai_aktual'] = actual_value
            
            # Find best metode (lowest error)
            if actual_value:
                best_metode = None
                best_error = float('inf')
                
                for key, data in results.items():
                    if 'error' not in data and 'error_persentase' in data:
                        if data['error_persentase'] < best_error:
                            best_error = data['error_persentase']
                            best_metode = key
                
                results['recommendation'] = best_metode
            
            return APIResponse.success(
                data=results,
                message='Perbandingan metode prediksi berhasil dibuat'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat membandingkan metode',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HybridPrediksiView(APIView):
    """
    API endpoint untuk prediksi menggunakan Hybrid Approach
    Menggabungkan TES + Business Rules + Monthly MAPE
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request):
        """
        Generate prediksi menggunakan Hybrid Approach
        
        Body:
        {
            "jenis_kendaraan_id": int (optional),
            "tahun_prediksi": int,
            "bulan_prediksi": int,
            "training_periods": int (optional, default: 24),
            "selected_scenario": str (optional, default: "base"),
            "save_to_db": bool (optional, default: false)
        }
        """
        try:
            jenis_kendaraan_id = request.data.get('jenis_kendaraan_id')
            tahun_prediksi = request.data.get('tahun_prediksi')
            bulan_prediksi = request.data.get('bulan_prediksi')
            training_periods = request.data.get('training_periods', 24)
            selected_scenario = request.data.get('selected_scenario', 'base')
            save_to_db = request.data.get('save_to_db', False)
            
            # Validasi
            if not tahun_prediksi or not bulan_prediksi:
                return APIResponse.error(
                    message='Tahun dan bulan prediksi harus diisi',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if selected_scenario not in ['conservative', 'base', 'moderate', 'optimistic']:
                selected_scenario = 'base'
            
            # Convert jenis_kendaraan_id
            jenis_kendaraan = None
            if jenis_kendaraan_id:
                try:
                    jenis_kendaraan = JenisKendaraan.objects.get(pk=jenis_kendaraan_id)
                except JenisKendaraan.DoesNotExist:
                    return APIResponse.error(
                        message='Jenis kendaraan tidak ditemukan',
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            
            # Generate hybrid prediction
            result = HybridPredictionService.predict_hybrid(
                tahun_prediksi=tahun_prediksi,
                bulan_prediksi=bulan_prediksi,
                jenis_kendaraan_id=jenis_kendaraan_id,
                training_periods=training_periods,
                selected_scenario=selected_scenario,
                return_details=True
            )
            
            # Save to database jika diminta
            if save_to_db:
                hasil_prediksi = HasilPrediksi.objects.create(
                    jenis_kendaraan=jenis_kendaraan,
                    tahun_prediksi=tahun_prediksi,
                    bulan_prediksi=bulan_prediksi,
                    metode=f'HYBRID_{selected_scenario.upper()}',
                    nilai_prediksi=result['nilai_prediksi'],
                    alpha=result['tes_parameters']['alpha'],
                    beta=result['tes_parameters']['beta'],
                    gamma=result['tes_parameters']['gamma'],
                    seasonal_periods=12,
                    mape=result.get('mape'),
                    mae=result.get('mae'),
                    rmse=result.get('rmse'),
                    nilai_aktual=result.get('nilai_aktual'),
                    data_training_dari=result['data_training_dari'],
                    data_training_sampai=result['data_training_sampai'],
                    jumlah_data_training=result['jumlah_data_training'],
                    keterangan=result.get('keterangan', '')
                )
                
                result['id'] = hasil_prediksi.id
                result['created_at'] = hasil_prediksi.created_at
            
            return APIResponse.success(
                data=result,
                message='Prediksi hybrid berhasil dihasilkan',
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat generate prediksi hybrid',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
