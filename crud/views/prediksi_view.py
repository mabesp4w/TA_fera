from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from crud.models import HasilPrediksi, AgregatPendapatanBulanan, JenisKendaraan
from crud.serializers.hasil_prediksi_serializer import HasilPrediksiSerializer
from crud.services.prediction_service import PredictionService
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
            
            # Save to database
            hasil_prediksi = HasilPrediksi.objects.create(
                jenis_kendaraan=jenis_kendaraan,
                tahun_prediksi=tahun_prediksi,
                bulan_prediksi=bulan_prediksi,
                metode=metode,
                nilai_prediksi=result['nilai_prediksi'],
                alpha=result['alpha'],
                beta=result.get('beta'),
                gamma=result.get('gamma'),
                seasonal_periods=result.get('seasonal_periods'),
                mape=result.get('mape'),
                mae=result.get('mae'),
                rmse=result.get('rmse'),
                nilai_aktual=result.get('nilai_aktual'),
                data_training_dari=result['data_training_dari'],
                data_training_sampai=result['data_training_sampai'],
                jumlah_data_training=result['jumlah_data_training'],
                keterangan=keterangan
            )
            
            serializer = HasilPrediksiSerializer(hasil_prediksi)
            return APIResponse.success(
                data=serializer.data,
                message=f'Prediksi menggunakan {metode} berhasil dibuat',
                status_code=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat generate prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComparePrediksiView(APIView):
    """
    API endpoint untuk membandingkan ketiga metode prediksi
    POST: Bandingkan SES, DES, dan TES
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request):
        """
        Bandingkan ketiga metode prediksi
        
        Body:
        {
            "jenis_kendaraan_id": int (optional),
            "tahun_prediksi": int,
            "bulan_prediksi": int
        }
        """
        try:
            jenis_kendaraan_id = request.data.get('jenis_kendaraan_id')
            tahun_prediksi = request.data.get('tahun_prediksi')
            bulan_prediksi = request.data.get('bulan_prediksi')
            
            if not tahun_prediksi or not bulan_prediksi:
                return APIResponse.error(
                    message='Tahun dan bulan prediksi harus diisi',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Compare methods
            comparison = PredictionService.compare_methods(
                jenis_kendaraan_id=jenis_kendaraan_id,
                tahun_prediksi=tahun_prediksi,
                bulan_prediksi=bulan_prediksi
            )
            
            # Format results untuk response
            formatted_results = {}
            for method, result in comparison['results'].items():
                if 'error' in result:
                    formatted_results[method] = {'error': result['error']}
                else:
                    formatted_results[method] = {
                        'nilai_prediksi': float(result['nilai_prediksi']),
                        'alpha': float(result['alpha']) if result['alpha'] else None,
                        'beta': float(result['beta']) if result.get('beta') else None,
                        'gamma': float(result['gamma']) if result.get('gamma') else None,
                        'mape': float(result['mape']) if result.get('mape') else None,
                        'mae': float(result['mae']) if result.get('mae') else None,
                        'rmse': float(result['rmse']) if result.get('rmse') else None,
                        'jumlah_data_training': result['jumlah_data_training']
                    }
            
            return APIResponse.success(
                data={
                    'results': formatted_results,
                    'best_method': comparison['best_method'],
                    'best_mape': comparison['best_mape'],
                    'recommendation': comparison['recommendation']
                },
                message='Perbandingan metode prediksi berhasil dibuat'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat membandingkan metode prediksi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrediksiChartView(APIView):
    """
    API endpoint untuk data chart/visualisasi prediksi
    GET: Data untuk chart (aktual vs prediksi)
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get data untuk chart
        
        Query Params:
        - jenis_kendaraan_id (optional)
        - tahun (optional) - filter by tahun
        - metode (optional) - filter by metode (SES, DES, TES)
        - limit (optional) - jumlah data terakhir (default: 24)
        """
        try:
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id')
            tahun = request.query_params.get('tahun')
            metode = request.query_params.get('metode')
            limit = int(request.query_params.get('limit', 24))
            
            # Get historical data (aktual)
            historical = PredictionService.get_historical_data(
                jenis_kendaraan_id=jenis_kendaraan_id
            )
            
            # Filter by tahun jika ada
            if tahun:
                historical = [h for h in historical if h['tahun'] == int(tahun)]
            
            # Limit data
            historical = historical[-limit:] if len(historical) > limit else historical
            
            # Get predictions
            predictions_query = HasilPrediksi.objects.select_related('jenis_kendaraan').all()
            
            if jenis_kendaraan_id:
                predictions_query = predictions_query.filter(jenis_kendaraan_id=jenis_kendaraan_id)
            
            if metode:
                predictions_query = predictions_query.filter(metode=metode)
            
            if tahun:
                predictions_query = predictions_query.filter(tahun_prediksi=int(tahun))
            
            predictions = predictions_query.order_by('tahun_prediksi', 'bulan_prediksi')[:limit]
            
            # Format data untuk chart
            chart_data = {
                'labels': [],
                'aktual': [],
                'prediksi': {
                    'SES': [],
                    'DES': [],
                    'TES': []
                }
            }
            
            # Add historical data
            for item in historical:
                label = f"{item['tahun']}-{item['bulan']:02d}"
                chart_data['labels'].append(label)
                chart_data['aktual'].append(item['total_pendapatan'])
                # Initialize prediction arrays
                chart_data['prediksi']['SES'].append(None)
                chart_data['prediksi']['DES'].append(None)
                chart_data['prediksi']['TES'].append(None)
            
            # Add predictions
            for pred in predictions:
                label = f"{pred.tahun_prediksi}-{pred.bulan_prediksi:02d}"
                if label in chart_data['labels']:
                    idx = chart_data['labels'].index(label)
                    chart_data['prediksi'][pred.metode][idx] = float(pred.nilai_prediksi)
                else:
                    # Add new label if not exists
                    chart_data['labels'].append(label)
                    chart_data['aktual'].append(None)
                    chart_data['prediksi']['SES'].append(None)
                    chart_data['prediksi']['DES'].append(None)
                    chart_data['prediksi']['TES'].append(None)
                    idx = len(chart_data['labels']) - 1
                    chart_data['prediksi'][pred.metode][idx] = float(pred.nilai_prediksi)
            
            return APIResponse.success(
                data=chart_data,
                message='Data chart berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data chart',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrediksiEvaluationView(APIView):
    """
    API endpoint untuk evaluasi akurasi model prediksi
    GET: Evaluasi akurasi berdasarkan MAPE, MAE, RMSE
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get evaluasi akurasi model
        
        Query Params:
        - jenis_kendaraan_id (optional)
        - metode (optional) - filter by metode
        - tahun (optional) - filter by tahun
        """
        try:
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id')
            metode = request.query_params.get('metode')
            tahun = request.query_params.get('tahun')
            
            # Query predictions dengan nilai_aktual
            queryset = HasilPrediksi.objects.select_related('jenis_kendaraan').filter(
                nilai_aktual__isnull=False
            )
            
            if jenis_kendaraan_id:
                queryset = queryset.filter(jenis_kendaraan_id=jenis_kendaraan_id)
            
            if metode:
                queryset = queryset.filter(metode=metode)
            
            if tahun:
                queryset = queryset.filter(tahun_prediksi=int(tahun))
            
            predictions = queryset.order_by('-tahun_prediksi', '-bulan_prediksi')
            
            # Group by metode
            evaluation = {}
            for pred in predictions:
                method = pred.metode
                if method not in evaluation:
                    evaluation[method] = {
                        'total': 0,
                        'total_mape': 0,
                        'total_mae': 0,
                        'total_rmse': 0,
                        'predictions': []
                    }
                
                evaluation[method]['total'] += 1
                if pred.mape:
                    evaluation[method]['total_mape'] += float(pred.mape)
                if pred.mae:
                    evaluation[method]['total_mae'] += float(pred.mae)
                if pred.rmse:
                    evaluation[method]['total_rmse'] += float(pred.rmse)
                
                evaluation[method]['predictions'].append({
                    'id': pred.id,
                    'tahun': pred.tahun_prediksi,
                    'bulan': pred.bulan_prediksi,
                    'prediksi': float(pred.nilai_prediksi),
                    'aktual': float(pred.nilai_aktual),
                    'mape': float(pred.mape) if pred.mape else None,
                    'mae': float(pred.mae) if pred.mae else None,
                    'rmse': float(pred.rmse) if pred.rmse else None,
                    'akurasi_persen': pred.akurasi_persen,
                    'selisih': pred.selisih
                })
            
            # Calculate averages
            for method, data in evaluation.items():
                if data['total'] > 0:
                    data['avg_mape'] = data['total_mape'] / data['total']
                    data['avg_mae'] = data['total_mae'] / data['total']
                    data['avg_rmse'] = data['total_rmse'] / data['total']
                    data['avg_akurasi'] = 100 - data['avg_mape']
                else:
                    data['avg_mape'] = None
                    data['avg_mae'] = None
                    data['avg_rmse'] = None
                    data['avg_akurasi'] = None
            
            # Determine best method
            best_method = None
            best_mape = float('inf')
            for method, data in evaluation.items():
                if data.get('avg_mape') and data['avg_mape'] < best_mape:
                    best_mape = data['avg_mape']
                    best_method = method
            
            return APIResponse.success(
                data={
                    'evaluation': evaluation,
                    'best_method': best_method,
                    'best_avg_mape': best_mape if best_method else None,
                    'summary': {
                        'total_predictions_evaluated': sum(d['total'] for d in evaluation.values()),
                        'methods_tested': list(evaluation.keys())
                    }
                },
                message='Evaluasi akurasi model berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil evaluasi akurasi',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrediksiTrendView(APIView):
    """
    API endpoint untuk melihat trend pendapatan
    GET: Data trend pendapatan historis
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """
        Get data trend pendapatan
        
        Query Params:
        - jenis_kendaraan_id (optional)
        - start_year (optional)
        - end_year (optional)
        - limit (optional) - jumlah data terakhir
        """
        try:
            jenis_kendaraan_id = request.query_params.get('jenis_kendaraan_id')
            start_year = request.query_params.get('start_year')
            end_year = request.query_params.get('end_year')
            limit = request.query_params.get('limit')
            
            # Get historical data
            historical = PredictionService.get_historical_data(
                jenis_kendaraan_id=jenis_kendaraan_id
            )
            
            # Filter by year range
            if start_year:
                historical = [h for h in historical if h['tahun'] >= int(start_year)]
            if end_year:
                historical = [h for h in historical if h['tahun'] <= int(end_year)]
            
            # Limit if specified
            if limit:
                historical = historical[-int(limit):]
            
            # Calculate statistics
            values = [h['total_pendapatan'] for h in historical]
            if values:
                import numpy as np
                trend_data = {
                    'data': historical,
                    'statistics': {
                        'min': float(np.min(values)),
                        'max': float(np.max(values)),
                        'mean': float(np.mean(values)),
                        'median': float(np.median(values)),
                        'std': float(np.std(values)),
                        'total_periods': len(historical)
                    },
                    'trend': 'increasing' if values[-1] > values[0] else 'decreasing' if values[-1] < values[0] else 'stable'
                }
            else:
                trend_data = {
                    'data': [],
                    'statistics': None,
                    'trend': None
                }
            
            return APIResponse.success(
                data=trend_data,
                message='Data trend pendapatan berhasil diambil'
            )
            
        except Exception as e:
            return APIResponse.error(
                message='Terjadi kesalahan saat mengambil data trend',
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

