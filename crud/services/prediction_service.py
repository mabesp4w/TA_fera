"""
Service utama untuk melakukan prediksi pendapatan pajak kendaraan
Menggunakan data dari AgregatPendapatanBulanan dan algoritma Exponential Smoothing
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from django.db.models import Q

from crud.models import AgregatPendapatanBulanan, HasilPrediksi, JenisKendaraan
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
    def get_historical_data(jenis_kendaraan_id: Optional[int] = None,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None,
                           min_periods: int = 12) -> List[Dict]:
        """
        Mengambil data historis dari AgregatPendapatanBulanan
        
        Args:
            jenis_kendaraan_id: Filter by jenis kendaraan (None = semua)
            start_date: Tanggal mulai (None = tidak dibatasi)
            end_date: Tanggal akhir (None = tidak dibatasi)
            min_periods: Minimum periode data yang diperlukan
        
        Returns:
            List dictionary dengan keys: tahun, bulan, total_pendapatan
        """
        queryset = AgregatPendapatanBulanan.objects.all()
        
        if jenis_kendaraan_id:
            queryset = queryset.filter(jenis_kendaraan_id=jenis_kendaraan_id)
        
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
        
        # Jika tidak ada filter date, ambil semua data
        
        # Order by tahun dan bulan
        queryset = queryset.order_by('tahun', 'bulan')
        
        data = []
        for item in queryset:
            data.append({
                'tahun': item.tahun,
                'bulan': item.bulan,
                'total_pendapatan': float(item.total_pendapatan),
                'jenis_kendaraan_id': item.jenis_kendaraan_id if item.jenis_kendaraan else None
            })
        
        if len(data) < min_periods:
            raise ValueError(
                f"Data historis tidak cukup. Minimal {min_periods} periode, "
                f"tetapi hanya ada {len(data)} periode"
            )
        
        return data
    
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
        # Get historical data
        historical = PredictionService.get_historical_data(jenis_kendaraan_id=jenis_kendaraan_id)
        values = [d['total_pendapatan'] for d in historical]
        
        # Calculate prediction
        prediction, alpha_opt, info = SimpleExponentialSmoothing.predict(
            values, alpha=alpha, optimize=optimize
        )
        
        # Calculate metrics (jika ada data aktual untuk periode sebelumnya)
        metrics = None
        if len(historical) >= 2:
            # Gunakan data terakhir sebagai "aktual" untuk validasi
            actual = values[-1]
            predicted_prev = info['forecast_values'][-1]
            metrics = calculate_all_metrics([actual], [predicted_prev])
        
        # Determine date range
        start_date = date(historical[0]['tahun'], historical[0]['bulan'], 1)
        end_date = date(historical[-1]['tahun'], historical[-1]['bulan'], 1)
        
        result = {
            'nilai_prediksi': Decimal(str(prediction)),
            'metode': 'SES',
            'alpha': Decimal(str(alpha_opt)),
            'beta': None,
            'gamma': None,
            'seasonal_periods': None,
            'mape': Decimal(str(metrics['mape'])) if metrics else None,
            'mae': Decimal(str(metrics['mae'])) if metrics else None,
            'rmse': Decimal(str(metrics['rmse'])) if metrics else None,
            'data_training_dari': start_date,
            'data_training_sampai': end_date,
            'jumlah_data_training': len(historical),
            'info': info
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
        # Get historical data
        historical = PredictionService.get_historical_data(
            jenis_kendaraan_id=jenis_kendaraan_id,
            min_periods=3
        )
        values = [d['total_pendapatan'] for d in historical]
        
        # Calculate prediction
        prediction, alpha_opt, beta_opt, info = DoubleExponentialSmoothing.predict(
            values, alpha=alpha, beta=beta, optimize=optimize
        )
        
        # Calculate metrics
        metrics = None
        if len(historical) >= 3:
            # Forecast untuk validasi
            forecast_prev = info['level_values'][-1] + info['trend_values'][-1]
            actual = values[-1]
            metrics = calculate_all_metrics([actual], [forecast_prev])
        
        # Determine date range
        start_date = date(historical[0]['tahun'], historical[0]['bulan'], 1)
        end_date = date(historical[-1]['tahun'], historical[-1]['bulan'], 1)
        
        result = {
            'nilai_prediksi': Decimal(str(prediction)),
            'metode': 'DES',
            'alpha': Decimal(str(alpha_opt)),
            'beta': Decimal(str(beta_opt)),
            'gamma': None,
            'seasonal_periods': None,
            'mape': Decimal(str(metrics['mape'])) if metrics else None,
            'mae': Decimal(str(metrics['mae'])) if metrics else None,
            'rmse': Decimal(str(metrics['rmse'])) if metrics else None,
            'data_training_dari': start_date,
            'data_training_sampai': end_date,
            'jumlah_data_training': len(historical),
            'info': info
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
        # Get historical data
        min_periods = 2 * seasonal_periods
        historical = PredictionService.get_historical_data(
            jenis_kendaraan_id=jenis_kendaraan_id,
            min_periods=min_periods
        )
        values = [d['total_pendapatan'] for d in historical]
        
        # Calculate prediction
        prediction, alpha_opt, beta_opt, gamma_opt, info = TripleExponentialSmoothing.predict(
            values,
            seasonal_periods=seasonal_periods,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            optimize=optimize
        )
        
        # Calculate metrics
        metrics = None
        if len(historical) >= min_periods + 1:
            # Forecast untuk validasi
            h = 1
            m = (len(values) + h - 1) % seasonal_periods
            forecast_prev = (info['level_values'][-seasonal_periods] + 
                           info['trend_values'][-seasonal_periods]) * info['seasonal_values'][-seasonal_periods + m]
            actual = values[-1]
            metrics = calculate_all_metrics([actual], [forecast_prev])
        
        # Determine date range
        start_date = date(historical[0]['tahun'], historical[0]['bulan'], 1)
        end_date = date(historical[-1]['tahun'], historical[-1]['bulan'], 1)
        
        result = {
            'nilai_prediksi': Decimal(str(prediction)),
            'metode': 'TES',
            'alpha': Decimal(str(alpha_opt)),
            'beta': Decimal(str(beta_opt)),
            'gamma': Decimal(str(gamma_opt)),
            'seasonal_periods': seasonal_periods,
            'mape': Decimal(str(metrics['mape'])) if metrics else None,
            'mae': Decimal(str(metrics['mae'])) if metrics else None,
            'rmse': Decimal(str(metrics['rmse'])) if metrics else None,
            'data_training_dari': start_date,
            'data_training_sampai': end_date,
            'jumlah_data_training': len(historical),
            'info': info
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

