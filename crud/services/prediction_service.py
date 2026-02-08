"""
Service utama untuk melakukan prediksi pendapatan pajak kendaraan
Menggunakan data dari AgregatPendapatanBulanan dan algoritma Exponential Smoothing
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from django.db.models import Q

from crud.models import AgregatPendapatanBulanan, HasilPrediksi, JenisKendaraan, TransaksiPajak
from django.db.models import Sum
from crud.services.exponential_smoothing import (
    SimpleExponentialSmoothing,
    DoubleExponentialSmoothing,
    TripleExponentialSmoothing
)
from crud.utils.metrics import calculate_all_metrics


class PredictionService:
    """
    Service untuk melakukan prediksi pendapatan pajak kendaraan
    """
    
    @staticmethod
    def get_actual_value(tahun: int, bulan: int, jenis_kendaraan_id: Optional[int] = None) -> Optional[float]:
        """
        Mendapatkan nilai aktual dari AgregatPendapatanBulanan untuk periode tertentu
        Menggunakan data agregat yang sudah dinormalisasi agar konsisten
        dengan data training.
        
        Args:
            tahun: Tahun
            bulan: Bulan
            jenis_kendaraan_id: ID jenis kendaraan (None = semua)
        
        Returns:
            Nilai aktual atau None jika tidak ada data
        """
        queryset = AgregatPendapatanBulanan.objects.filter(
            tahun=tahun,
            bulan=bulan
        )
        
        if jenis_kendaraan_id is not None:
            queryset = queryset.filter(jenis_kendaraan_id=jenis_kendaraan_id)
        else:
            queryset = queryset.filter(jenis_kendaraan__isnull=True)
        
        result = queryset.first()
        if result and result.total_pendapatan:
            return float(result.total_pendapatan)
        return None
    
    @staticmethod
    def get_historical_data(jenis_kendaraan_id: Optional[int] = None,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None,
                           min_periods: int = 12,
                           use_realtime: bool = False) -> List[Dict]:
        """
        Mengambil data historis dari TransaksiPajak (real-time) atau AgregatPendapatanBulanan
        
        Args:
            jenis_kendaraan_id: Filter by jenis kendaraan (None = semua)
            start_date: Tanggal mulai (None = tidak dibatasi)
            end_date: Tanggal akhir (None = tidak dibatasi)
            min_periods: Minimum periode data yang diperlukan
            use_realtime: Jika True, ambil data langsung dari TransaksiPajak
        
        Returns:
            List dictionary dengan keys: tahun, bulan, total_pendapatan
        """
        # Ambil data dari AgregatPendapatanBulanan (data lebih lengkap)
        queryset = AgregatPendapatanBulanan.objects.all()
        
        if jenis_kendaraan_id is not None:
            queryset = queryset.filter(jenis_kendaraan_id=jenis_kendaraan_id)
        else:
            # PERBAIKAN: Untuk query global, ambil hanya record yang jenis_kendaraan=NULL
            # Record NULL sudah berisi total keseluruhan, tidak perlu SUM lagi
            queryset = queryset.filter(jenis_kendaraan__isnull=True)
        
        # Filter by date range
        if start_date:
            queryset = queryset.filter(
                Q(tahun__gt=start_date.year) |
                (Q(tahun=start_date.year) & Q(bulan__gte=start_date.month))
            )
        
        if end_date:
            queryset = queryset.filter(
                Q(tahun__lt=end_date.year) |
                (Q(tahun=end_date.year) & Q(bulan__lte=end_date.month))
            )
        
        # Order by tahun dan bulan
        queryset = queryset.order_by('tahun', 'bulan')
        
        # Ambil data dari queryset
        data = []
        for item in queryset:
            data.append({
                'tahun': item.tahun,
                'bulan': item.bulan,
                'total_pendapatan': float(item.total_pendapatan),
                'jenis_kendaraan_id': item.jenis_kendaraan_id if item.jenis_kendaraan else None
            })
        
        # Jika data agregat tidak cukup atau use_realtime=True, coba ambil dari TransaksiPajak
        if len(data) < min_periods or use_realtime:
            transaksi_filter = {}
            if start_date:
                transaksi_filter['tahun__gte'] = start_date.year
            if end_date:
                transaksi_filter['tahun__lte'] = end_date.year
            
            transaksi_queryset = TransaksiPajak.objects.values(
                'tahun', 'bulan'
            ).annotate(
                total_pendapatan=Sum('total_bayar')
            ).order_by('tahun', 'bulan')
            
            if transaksi_filter:
                transaksi_queryset = transaksi_queryset.filter(**transaksi_filter)
            
            if jenis_kendaraan_id is not None:
                transaksi_queryset = transaksi_queryset.filter(kendaraan__jenis_id=jenis_kendaraan_id)
            
            realtime_data = []
            for item in transaksi_queryset:
                realtime_data.append({
                    'tahun': item['tahun'],
                    'bulan': item['bulan'],
                    'total_pendapatan': float(item['total_pendapatan'] or 0),
                    'jenis_kendaraan_id': jenis_kendaraan_id
                })
            
            # Gunakan realtime data jika lebih lengkap
            if len(realtime_data) > len(data):
                data = realtime_data
            
            # Aggregate jika jenis_kendaraan_id is None
            if jenis_kendaraan_id is None and data:
                from collections import defaultdict
                aggregated = defaultdict(float)
                for item in data:
                    key = (item['tahun'], item['bulan'])
                    aggregated[key] += item['total_pendapatan']
                
                data = []
                for (tahun, bulan), total in sorted(aggregated.items()):
                    data.append({
                        'tahun': tahun,
                        'bulan': bulan,
                        'total_pendapatan': total,
                        'jenis_kendaraan_id': None
                    })
        
        if len(data) < min_periods:
            raise ValueError(
                f"Data historis tidak cukup. Minimal {min_periods} periode, "
                f"tetapi hanya ada {len(data)} periode"
            )
        
        return data
    
    @staticmethod
    def _calculate_steps(historical: List[Dict], tahun_prediksi: int, bulan_prediksi: int) -> int:
        """
        Menghitung berapa langkah ke depan yang perlu diprediksi
        
        Args:
            historical: List data historis
            tahun_prediksi: Tahun target prediksi
            bulan_prediksi: Bulan target prediksi
        
        Returns:
            Jumlah langkah ke depan
        """
        if not historical:
            return 1
        
        # Data terakhir
        last_data = historical[-1]
        last_year = last_data['tahun']
        last_month = last_data['bulan']
        
        # Hitung selisih dalam bulan
        steps = (tahun_prediksi - last_year) * 12 + (bulan_prediksi - last_month)
        
        # Minimal 1 langkah
        return max(1, steps)
    
    @staticmethod
    def predict_ses(jenis_kendaraan_id: Optional[int] = None,
                   tahun_prediksi: int = None,
                   bulan_prediksi: int = None,
                   alpha: Optional[float] = None,
                   optimize: bool = True) -> Dict:
        """
        Melakukan prediksi menggunakan Simple Exponential Smoothing
        
        Args:
            jenis_kendaraan_id: ID jenis kendaraan (None = semua)
            tahun_prediksi: Tahun yang akan diprediksi
            bulan_prediksi: Bulan yang akan diprediksi
            alpha: Parameter alpha (None = akan dioptimasi)
            optimize: Optimasi parameter
        
        Returns:
            Dictionary dengan hasil prediksi
        """
        # PERBAIKAN: Exclude target period dari data training (mencegah data leakage)
        # Data training hanya sampai bulan SEBELUM target prediksi
        end_date = None
        if tahun_prediksi and bulan_prediksi:
            if bulan_prediksi == 1:
                end_date = date(tahun_prediksi - 1, 12, 1)
            else:
                end_date = date(tahun_prediksi, bulan_prediksi - 1, 1)
        
        historical = PredictionService.get_historical_data(
            jenis_kendaraan_id=jenis_kendaraan_id,
            end_date=end_date
        )
        values = [d['total_pendapatan'] for d in historical]
        
        # Hitung berapa langkah ke depan
        steps = PredictionService._calculate_steps(historical, tahun_prediksi, bulan_prediksi)
        
        # Calculate prediction
        prediction, alpha_opt, info = SimpleExponentialSmoothing.predict(
            values, alpha=alpha, optimize=optimize, steps=steps
        )
        
        # Ambil prediksi untuk langkah terakhir (target)
        if info.get('future_forecasts') and len(info['future_forecasts']) >= steps:
            prediction = info['future_forecasts'][steps - 1]
        
        # PERBAIKAN: Hitung MAPE in-sample dari fitted values (banyak titik data)
        # forecast_values[i] = alpha * data[i-1] + (1-alpha) * forecast[i-1] → 1-step ahead forecast
        forecast_values = info['forecast_values']
        if len(values) > 1:
            metrics = calculate_all_metrics(values[1:], forecast_values[1:])
        else:
            metrics = {'mape': 0.0, 'mae': 0.0, 'rmse': 0.0}
        
        # Cek apakah ada nilai aktual untuk periode yang diprediksi (untuk validasi)
        actual_value = PredictionService.get_actual_value(
            tahun_prediksi, bulan_prediksi, jenis_kendaraan_id
        )
        
        debug_info = {
            'actual_value_found': actual_value is not None,
            'metrics_type': 'in-sample',
            'metrics_data_points': len(values) - 1,
        }
        
        if actual_value is not None:
            error_aktual = abs((actual_value - prediction) / actual_value) * 100
            debug_info['actual_value'] = actual_value
            debug_info['prediction'] = prediction
            debug_info['error_vs_actual'] = error_aktual
        
        # Determine date range
        start_date = date(historical[0]['tahun'], historical[0]['bulan'], 1)
        end_date_result = date(historical[-1]['tahun'], historical[-1]['bulan'], 1)
        
        result = {
            'nilai_prediksi': Decimal(str(prediction)),
            'metode': 'SES',
            'alpha': Decimal(str(alpha_opt)),
            'beta': None,
            'gamma': None,
            'seasonal_periods': None,
            'mape': Decimal(str(metrics['mape'])),
            'mae': Decimal(str(metrics['mae'])),
            'rmse': Decimal(str(metrics['rmse'])),
            'data_training_dari': start_date,
            'data_training_sampai': end_date_result,
            'jumlah_data_training': len(historical),
            'nilai_aktual': Decimal(str(actual_value)) if actual_value is not None else None,
            'info': info,
            'debug': debug_info
        }
        
        return result
    
    @staticmethod
    def predict_des(jenis_kendaraan_id: Optional[int] = None,
                   tahun_prediksi: int = None,
                   bulan_prediksi: int = None,
                   alpha: Optional[float] = None,
                   beta: Optional[float] = None,
                   optimize: bool = True) -> Dict:
        """
        Melakukan prediksi menggunakan Double Exponential Smoothing
        
        Args:
            jenis_kendaraan_id: ID jenis kendaraan (None = semua)
            tahun_prediksi: Tahun yang akan diprediksi
            bulan_prediksi: Bulan yang akan diprediksi
            alpha: Parameter alpha (None = akan dioptimasi)
            beta: Parameter beta (None = akan dioptimasi)
            optimize: Optimasi parameter
        
        Returns:
            Dictionary dengan hasil prediksi
        """
        # PERBAIKAN: Exclude target period dari data training (mencegah data leakage)
        end_date = None
        if tahun_prediksi and bulan_prediksi:
            if bulan_prediksi == 1:
                end_date = date(tahun_prediksi - 1, 12, 1)
            else:
                end_date = date(tahun_prediksi, bulan_prediksi - 1, 1)
        
        historical = PredictionService.get_historical_data(
            jenis_kendaraan_id=jenis_kendaraan_id,
            end_date=end_date,
            min_periods=3
        )
        values = [d['total_pendapatan'] for d in historical]
        
        # Hitung berapa langkah ke depan
        steps = PredictionService._calculate_steps(historical, tahun_prediksi, bulan_prediksi)
        
        # Calculate prediction
        prediction, alpha_opt, beta_opt, info = DoubleExponentialSmoothing.predict(
            values, alpha=alpha, beta=beta, optimize=optimize, steps=steps
        )
        
        # Ambil prediksi untuk langkah terakhir (target)
        if info.get('future_forecasts') and len(info['future_forecasts']) >= steps:
            prediction = info['future_forecasts'][steps - 1]
        
        # PERBAIKAN: Hitung MAPE in-sample dari fitted values (statsmodels)
        forecast_values = info['forecast_values']
        if len(values) > 1:
            metrics = calculate_all_metrics(values[1:], forecast_values[1:])
        else:
            metrics = {'mape': 0.0, 'mae': 0.0, 'rmse': 0.0}
        
        # Cek apakah ada nilai aktual untuk periode yang diprediksi (untuk validasi)
        actual_value = PredictionService.get_actual_value(
            tahun_prediksi, bulan_prediksi, jenis_kendaraan_id
        )
        
        debug_info = {
            'actual_value_found': actual_value is not None,
            'metrics_type': 'in-sample',
            'metrics_data_points': len(values) - 1,
        }
        
        if actual_value is not None:
            error_aktual = abs((actual_value - prediction) / actual_value) * 100
            debug_info['actual_value'] = actual_value
            debug_info['prediction'] = prediction
            debug_info['error_vs_actual'] = error_aktual
        
        # Determine date range
        start_date = date(historical[0]['tahun'], historical[0]['bulan'], 1)
        end_date_result = date(historical[-1]['tahun'], historical[-1]['bulan'], 1)
        
        result = {
            'nilai_prediksi': Decimal(str(prediction)),
            'metode': 'DES',
            'alpha': Decimal(str(alpha_opt)),
            'beta': Decimal(str(beta_opt)),
            'gamma': None,
            'seasonal_periods': None,
            'mape': Decimal(str(metrics['mape'])),
            'mae': Decimal(str(metrics['mae'])),
            'rmse': Decimal(str(metrics['rmse'])),
            'data_training_dari': start_date,
            'data_training_sampai': end_date_result,
            'jumlah_data_training': len(historical),
            'nilai_aktual': Decimal(str(actual_value)) if actual_value is not None else None,
            'info': info,
            'debug': debug_info
        }
        
        return result
    
    @staticmethod
    def predict_tes(jenis_kendaraan_id: Optional[int] = None,
                   tahun_prediksi: int = None,
                   bulan_prediksi: int = None,
                   seasonal_periods: int = 12,
                   alpha: Optional[float] = None,
                   beta: Optional[float] = None,
                   gamma: Optional[float] = None,
                   optimize: bool = True) -> Dict:
        """
        Melakukan prediksi menggunakan Triple Exponential Smoothing
        
        Args:
            jenis_kendaraan_id: ID jenis kendaraan (None = semua)
            tahun_prediksi: Tahun yang akan diprediksi
            bulan_prediksi: Bulan yang akan diprediksi
            seasonal_periods: Periode musiman (default: 12 untuk bulanan)
            alpha: Parameter alpha (None = akan dioptimasi)
            beta: Parameter beta (None = akan dioptimasi)
            gamma: Parameter gamma (None = akan dioptimasi)
            optimize: Optimasi parameter
        
        Returns:
            Dictionary dengan hasil prediksi
        """
        # PERBAIKAN: Exclude target period dari data training (mencegah data leakage)
        end_date = None
        if tahun_prediksi and bulan_prediksi:
            if bulan_prediksi == 1:
                end_date = date(tahun_prediksi - 1, 12, 1)
            else:
                end_date = date(tahun_prediksi, bulan_prediksi - 1, 1)
        
        min_periods = 2 * seasonal_periods
        historical = PredictionService.get_historical_data(
            jenis_kendaraan_id=jenis_kendaraan_id,
            end_date=end_date,
            min_periods=min_periods
        )
        values = [d['total_pendapatan'] for d in historical]
        
        # Hitung berapa langkah ke depan
        steps = PredictionService._calculate_steps(historical, tahun_prediksi, bulan_prediksi)
        
        # Calculate prediction
        prediction, alpha_opt, beta_opt, gamma_opt, info = TripleExponentialSmoothing.predict(
            values,
            seasonal_periods=seasonal_periods,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            optimize=optimize,
            steps=steps
        )
        
        # Ambil prediksi untuk langkah terakhir (target)
        if info.get('future_forecasts') and len(info['future_forecasts']) >= steps:
            prediction = info['future_forecasts'][steps - 1]
        
        # PERBAIKAN: Hitung MAPE in-sample dari fitted values (statsmodels)
        # Skip periode seasonal pertama karena belum ada seasonal component
        forecast_values = info['forecast_values']
        skip = seasonal_periods
        if len(values) > skip:
            metrics = calculate_all_metrics(values[skip:], forecast_values[skip:])
        else:
            metrics = {'mape': 0.0, 'mae': 0.0, 'rmse': 0.0}
        
        # Cek apakah ada nilai aktual untuk periode yang diprediksi (untuk validasi)
        actual_value = PredictionService.get_actual_value(
            tahun_prediksi, bulan_prediksi, jenis_kendaraan_id
        )
        
        debug_info = {
            'actual_value_found': actual_value is not None,
            'metrics_type': 'in-sample',
            'metrics_data_points': len(values) - skip,
            'best_config': info.get('best_config', 'unknown'),
        }
        
        if actual_value is not None:
            error_aktual = abs((actual_value - prediction) / actual_value) * 100
            debug_info['actual_value'] = actual_value
            debug_info['prediction'] = prediction
            debug_info['error_vs_actual'] = error_aktual
        
        # Determine date range
        start_date = date(historical[0]['tahun'], historical[0]['bulan'], 1)
        end_date_result = date(historical[-1]['tahun'], historical[-1]['bulan'], 1)
        
        result = {
            'nilai_prediksi': Decimal(str(prediction)),
            'metode': 'TES',
            'alpha': Decimal(str(alpha_opt)),
            'beta': Decimal(str(beta_opt)),
            'gamma': Decimal(str(gamma_opt)),
            'seasonal_periods': seasonal_periods,
            'mape': Decimal(str(metrics['mape'])),
            'mae': Decimal(str(metrics['mae'])),
            'rmse': Decimal(str(metrics['rmse'])),
            'data_training_dari': start_date,
            'data_training_sampai': end_date_result,
            'jumlah_data_training': len(historical),
            'nilai_aktual': Decimal(str(actual_value)) if actual_value is not None else None,
            'info': info,
            'debug': debug_info
        }
        
        return result
    
    @staticmethod
    def compare_methods(jenis_kendaraan_id: Optional[int] = None,
                       tahun_prediksi: int = None,
                       bulan_prediksi: int = None) -> Dict:
        """
        Membandingkan ketiga metode (SES, DES, TES) dan return yang terbaik
        
        Args:
            jenis_kendaraan_id: ID jenis kendaraan (None = semua)
            tahun_prediksi: Tahun yang akan diprediksi
            bulan_prediksi: Bulan yang akan diprediksi
        
        Returns:
            Dictionary dengan hasil semua metode dan rekomendasi metode terbaik
        """
        results = {}
        
        # SES
        try:
            ses_result = PredictionService.predict_ses(
                jenis_kendaraan_id=jenis_kendaraan_id,
                tahun_prediksi=tahun_prediksi,
                bulan_prediksi=bulan_prediksi
            )
            results['SES'] = ses_result
        except Exception as e:
            results['SES'] = {'error': str(e)}
        
        # DES
        try:
            des_result = PredictionService.predict_des(
                jenis_kendaraan_id=jenis_kendaraan_id,
                tahun_prediksi=tahun_prediksi,
                bulan_prediksi=bulan_prediksi
            )
            results['DES'] = des_result
        except Exception as e:
            results['DES'] = {'error': str(e)}
        
        # TES
        try:
            tes_result = PredictionService.predict_tes(
                jenis_kendaraan_id=jenis_kendaraan_id,
                tahun_prediksi=tahun_prediksi,
                bulan_prediksi=bulan_prediksi
            )
            results['TES'] = tes_result
        except Exception as e:
            results['TES'] = {'error': str(e)}
        
        # Tentukan metode terbaik berdasarkan MAPE (semakin kecil semakin baik)
        best_method = None
        best_mape = float('inf')
        
        for method, result in results.items():
            if 'error' not in result and result.get('mape'):
                mape = float(result['mape'])
                if mape < best_mape:
                    best_mape = mape
                    best_method = method
        
        return {
            'results': results,
            'best_method': best_method,
            'best_mape': best_mape if best_method else None,
            'recommendation': f"Metode terbaik: {best_method} dengan MAPE {best_mape:.2f}%" if best_method else "Tidak dapat menentukan metode terbaik"
        }

