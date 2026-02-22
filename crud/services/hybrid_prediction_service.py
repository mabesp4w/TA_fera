"""
Service untuk Hybrid Prediction Approach
Menggabungkan TES + Business Rules + Monthly MAPE untuk akurasi maksimal
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import numpy as np

from crud.models import AgregatPendapatanBulanan, HasilPrediksi
from crud.services.exponential_smoothing import (
    SimpleExponentialSmoothing,
    DoubleExponentialSmoothing,
    TripleExponentialSmoothing
)
from crud.services.prediction_service import PredictionService
from crud.utils.metrics import calculate_all_metrics


class HybridPredictionService:
    """
    Hybrid Prediction Service
    Menggabungkan:
    1. TES (Triple Exponential Smoothing) sebagai base prediction
    2. Monthly MAPE untuk scenario selection
    3. Business rules untuk monthly adjustment
    4. Scenario-based forecasting dengan realistic range
    """
    
    # Scenario configuration
    SCENARIOS = {
        'conservative': {
            'factor': 0.50,
            'description': 'Pessimistic - Untuk planning yang sangat hati-hati'
        },
        'base': {
            'factor': 0.65,
            'description': 'Moderate - Scenario dasar yang direkomendasikan'
        },
        'moderate': {
            'factor': 0.70,
            'description': 'Moderate-Optimistic - Untuk planning normal'
        },
        'optimistic': {
            'factor': 0.80,
            'description': 'Optimistic - Untuk target agresif'
        }
    }
    
    # Monthly adjustment rules (berdasarkan faktor bisnis)
    MONTHLY_ADJUSTMENTS = {
        1: 0.95,   # Januari (relaksasi akhir tahun)
        2: 1.00,   # Februari
        3: 0.95,   # Maret (akhir Q1)
        4: 1.00,   # April
        5: 1.00,   # Mei
        6: 1.00,   # Juni
        7: 1.05,   # Juli (mulai Q2 tinggi)
        8: 1.10,   # Agustus (peak season)
        9: 1.00,   # September
        10: 0.90,  # Oktober (cutoff program, biasanya turun)
        11: 1.00,  # November
        12: 1.05,  # Desember (akhir tahun, biasanya naik)
    }
    
    @staticmethod
    def get_historical_data(jenis_kendaraan_id: Optional[int] = None,
                           periods: int = 24,
                           end_date: Optional[date] = None,
                           min_periods: int = 12) -> List[Dict]:
        """
        Mengambil data historis N periode terakhir
        Default: 24 periode (2 tahun terakhir)

        Args:
            jenis_kendaraan_id: Filter by jenis kendaraan
            periods: Jumlah periode untuk menghitung start_date
            end_date: Tanggal akhir data
            min_periods: Minimal periode yang diperlukan (default: 12)
        """
        if end_date is None:
            end_date = date.today()

        start_date = end_date - timedelta(days=periods * 30)

        return PredictionService.get_historical_data(
            jenis_kendaraan_id=jenis_kendaraan_id,
            start_date=start_date,
            end_date=end_date,
            min_periods=min_periods
        )
    
    @staticmethod
    def get_monthly_mape(target_month: int,
                         target_year: int,
                         jenis_kendaraan_id: Optional[int] = None) -> Optional[float]:
        """
        Menghitung MAPE untuk bulan spesifik dari data historis
        """
        end_date = date(target_year, target_month, 1) - timedelta(days=1)

        # Ambil data untuk bulan yang sama dari tahun-tahun sebelumnya
        from crud.models import AgregatPendapatanBulanan, TransaksiPajak
        from django.db.models import Q, Sum

        data = AgregatPendapatanBulanan.objects.filter(
            bulan=target_month,
            tahun__gte=target_year - 3,
            tahun__lt=target_year
        )

        if jenis_kendaraan_id is not None:
            data = data.filter(jenis_kendaraan_id=jenis_kendaraan_id)
        else:
            data = data.filter(jenis_kendaraan__isnull=True)

        data = data.order_by('tahun')

        values = [float(d.total_pendapatan) for d in data]

        # Fallback ke TransaksiPajak jika data agregat tidak cukup
        if len(values) < 2:
            transaksi_data = TransaksiPajak.objects.filter(
                bulan=target_month,
                tahun__gte=target_year - 3,
                tahun__lt=target_year
            )

            if jenis_kendaraan_id is not None:
                transaksi_data = transaksi_data.filter(kendaraan__jenis_id=jenis_kendaraan_id)

            transaksi_data = transaksi_data.values('tahun').annotate(
                total_pendapatan=Sum('total_bayar')
            ).order_by('tahun')

            values = []
            for item in transaksi_data:
                if item['total_pendapatan']:
                    values.append(float(item['total_pendapatan']))

        if len(values) < 2:
            return None

        # Hitung MAPE sederhana (prediksi moving average vs aktual)
        # Use simple method: prediksi tahun ini = tahun lalu
        mape_values = []
        for i in range(1, len(values)):
            prediksi = float(values[i-1])  # Tahun lalu
            aktual = float(values[i])      # Tahun ini
            error_pct = abs(prediksi - aktual) / aktual * 100 if aktual > 0 else 0
            mape_values.append(error_pct)

        return float(np.mean(mape_values)) if mape_values else None
    
    @staticmethod
    def predict_hybrid(
        tahun_prediksi: int,
        bulan_prediksi: int,
        training_periods: int = 24,
        selected_scenario: str = 'base',
        jenis_kendaraan_id: Optional[int] = None,
        return_details: bool = False
    ) -> Dict:
        """
        Prediksi menggunakan Hybrid Approach

        Steps:
        1. Generate prediction sebagai base (TES jika cukup data, fallback ke DES/SES)
        2. Dapatkan Monthly MAPE untuk scenario selection
        3. Apply scenario factor berdasarkan Monthly MAPE
        4. Apply monthly adjustment rules
        5. Return prediction dengan realistic range

        Args:
            tahun_prediksi: Tahun prediksi
            bulan_prediksi: Bulan prediksi
            jenis_kendaraan_id: ID jenis kendaraan (None = semua)
            training_periods: Jumlah periode training (default: 24)
            selected_scenario: Scenario yang dipilih (conservative, base, moderate, optimistic)
            return_details: Jika True, return detail per scenario

        Returns:
            Dictionary dengan prediksi dan informasi detail
        """
        # Validasi scenario
        if selected_scenario not in HybridPredictionService.SCENARIOS:
            selected_scenario = 'base'

        # 1. Ambil data historis dengan fallback yang lebih cerdas
        end_date = date(tahun_prediksi, bulan_prediksi, 1) - timedelta(days=1)

        # Tentukan minimal periods berdasarkan metode yang mungkin digunakan
        # TES butuh 24, DES butuh 6, SES butuh 3
        min_periods_options = [24, 12, 6, 3]
        historical_data = None
        used_fallback = False
        actual_min_periods = None

        # Coba ambil data dengan minimal periods yang berbeda
        for min_p in min_periods_options:
            try:
                # Coba dengan jenis kendaraan spesifik dulu
                historical_data = HybridPredictionService.get_historical_data(
                    jenis_kendaraan_id=jenis_kendaraan_id,
                    periods=training_periods,
                    end_date=end_date,
                    min_periods=min_p
                )
                actual_min_periods = min_p
                used_fallback = False
                break
            except ValueError:
                # Jika gagal dan ada jenis_kendaraan_id spesifik, coba fallback ke data global
                if jenis_kendaraan_id is not None:
                    try:
                        historical_data = HybridPredictionService.get_historical_data(
                            jenis_kendaraan_id=None,  # Gunakan data global
                            periods=training_periods,
                            end_date=end_date,
                            min_periods=min_p
                        )
                        actual_min_periods = min_p
                        used_fallback = True
                        break
                    except ValueError:
                        continue
                else:
                    continue

        if historical_data is None:
            raise ValueError(
                f"Data historis tidak mencukupi untuk melakukan prediksi. "
                f"Dibutuhkan minimal 3 periode data."
            )

        values = [d['total_pendapatan'] for d in historical_data]

        # 2. Generate prediction sebagai base berdasarkan jumlah data yang tersedia
        # Pilih metode berdasarkan jumlah data
        if len(values) >= 24:
            # Gunakan TES untuk data >= 24 periode
            try:
                pred_tes, alpha, beta, gamma, info_tes = TripleExponentialSmoothing.predict(
                    values, seasonal_periods=12, optimize=True, steps=1
                )
                pred_base = pred_tes
                base_method = 'TES'
            except Exception as e:
                # Fallback ke DES jika TES gagal
                try:
                    pred_base, alpha, beta, info_tes = DoubleExponentialSmoothing.predict(
                        values, optimize=True, steps=1
                    )
                    gamma = 0
                    base_method = 'DES'
                except Exception:
                    # Fallback ke SES jika DES juga gagal
                    pred_base, alpha, info_tes = SimpleExponentialSmoothing.predict(
                        values, optimize=True, steps=1
                    )
                    beta = 0
                    gamma = 0
                    base_method = 'SES'
        elif len(values) >= 6:
            # Gunakan DES untuk data 6-23 periode
            pred_base, alpha, beta, info_tes = DoubleExponentialSmoothing.predict(
                values, optimize=True, steps=1
            )
            gamma = 0
            base_method = 'DES'
        else:
            # Gunakan SES untuk data 3-5 periode
            pred_base, alpha, info_tes = SimpleExponentialSmoothing.predict(
                values, optimize=True, steps=1
            )
            beta = 0
            gamma = 0
            base_method = 'SES'

        # 3. Dapatkan Monthly MAPE untuk scenario selection
        # Jika fallback digunakan, gunakan data global untuk MAPE juga
        mape_jenis_id = None if used_fallback else jenis_kendaraan_id
        monthly_mape = HybridPredictionService.get_monthly_mape(
            jenis_kendaraan_id=mape_jenis_id,
            target_month=bulan_prediksi,
            target_year=tahun_prediksi
        )
        
        # 4. Determine recommended scenario berdasarkan Monthly MAPE
        if monthly_mape is not None:
            if monthly_mape > 40:
                recommended_scenario = 'conservative'
            elif monthly_mape > 25:
                recommended_scenario = 'base'
            elif monthly_mape > 15:
                recommended_scenario = 'moderate'
            else:
                recommended_scenario = 'optimistic'
        else:
            recommended_scenario = 'base'
        
        # 5. Apply monthly adjustment rules
        monthly_adjustment = HybridPredictionService.MONTHLY_ADJUSTMENTS.get(bulan_prediksi, 1.0)

        # 6. Calculate predictions untuk semua scenarios
        scenarios_result = {}
        for scenario_name, scenario_config in HybridPredictionService.SCENARIOS.items():
            factor = scenario_config['factor']

            # Apply scenario factor dan monthly adjustment
            pred_scenario = pred_base * factor * monthly_adjustment
            scenarios_result[scenario_name] = {
                'prediksi': float(pred_scenario),
                'factor': float(factor),
                'monthly_adjustment': float(monthly_adjustment),
                'final_factor': float(factor * monthly_adjustment),
                'description': scenario_config['description']
            }

        # 7. Final prediction (gunakan scenario yang dipilih)
        final_prediction = scenarios_result[selected_scenario]['prediksi']

        # 8. Calculate metrics
        forecast_values = info_tes.get('forecast_values', [])
        start_idx = 12

        actual_aligned = values[start_idx:]
        forecast_aligned = forecast_values[start_idx:]

        metrics = {}
        if len(actual_aligned) > 0 and len(forecast_aligned) > 0:
            metrics = calculate_all_metrics(actual_aligned, forecast_aligned)

        # 9. Calculate confidence interval
        std_dev = np.std(values[-12:]) if len(values) >= 12 else np.std(values)
        confidence_lower = final_prediction - 2 * std_dev
        confidence_upper = final_prediction + 2 * std_dev

        # 10. Build result
        fallback_note = ' (menggunakan data global - data spesifik jenis kendaraan tidak cukup)' if used_fallback else ''
        base_method_note = f' (base method: {base_method}, data: {len(values)} periode)' if base_method != 'TES' else ''
        result = {
            'nilai_prediksi': final_prediction,
            'confidence_lower': max(0, confidence_lower),
            'confidence_upper': confidence_upper,
            'confidence_interval': 95,
            'metode': f'HYBRID_{base_method}',
            'base_method': base_method,
            'scenario': selected_scenario,
            'scenarios': scenarios_result,
            'recommended_scenario': recommended_scenario,
            'monthly_mape': monthly_mape,
            'monthly_adjustment': float(monthly_adjustment),
            'tes_prediction': pred_base,  # Renamed from pred_tes to pred_base
            'tes_parameters': {
                'alpha': alpha,
                'beta': beta,
                'gamma': gamma
            },
            'mape': metrics.get('mape', None),
            'mae': metrics.get('mae', None),
            'rmse': metrics.get('rmse', None),
            'data_training_dari': date(historical_data[0]['tahun'], historical_data[0]['bulan'], 1),
            'data_training_sampai': end_date,
            'jumlah_data_training': len(values),
            'training_periods': training_periods,
            'used_fallback': used_fallback,
            'keterangan': f'Hybrid prediction: {base_method} base ({len(values)} periode) + Scenario {selected_scenario} + Monthly Adjustment ({monthly_adjustment:.2f}){fallback_note}{base_method_note}'
        }
        
        # 11. Calculate actual error jika ada
        actual_value = PredictionService.get_actual_value(
            tahun_prediksi, bulan_prediksi, jenis_kendaraan_id
        )
        
        if actual_value is not None:
            # Konversi ke float untuk menghindari error Decimal - float
            actual_float = float(actual_value)
            final_prediction_float = float(final_prediction)
            error_abs = abs(final_prediction_float - actual_float)
            error_pct = (error_abs / actual_float * 100) if actual_float > 0 else 0

            result['nilai_aktual'] = actual_float
            result['error_absolut'] = error_abs
            result['error_persentase'] = error_pct
            result['akurasi'] = 100 - error_pct
        
        return result
