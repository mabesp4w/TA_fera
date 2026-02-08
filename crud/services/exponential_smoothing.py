"""
Implementasi algoritma Exponential Smoothing untuk prediksi
Menggunakan statsmodels untuk optimasi parameter yang lebih baik (MLE)

- Simple Exponential Smoothing (SES)
- Double Exponential Smoothing (DES/Holt)
- Triple Exponential Smoothing (TES/Holt-Winters)
"""
import numpy as np
import warnings
from typing import List, Tuple, Optional
from decimal import Decimal
from statsmodels.tsa.holtwinters import ExponentialSmoothing as HoltWinters


class SimpleExponentialSmoothing:
    """
    Simple Exponential Smoothing (SES)
    Cocok untuk data tanpa trend dan seasonality
    Menggunakan statsmodels untuk optimasi parameter MLE
    """
    
    @staticmethod
    def predict(data: List[float], alpha: Optional[float] = None, 
                optimize: bool = True, steps: int = 1) -> Tuple[float, float, dict]:
        """
        Melakukan prediksi menggunakan Simple Exponential Smoothing
        
        Args:
            data: List data historis
            alpha: Parameter smoothing (0-1), jika None akan dioptimasi
            optimize: Jika True, akan mencari alpha optimal
            steps: Jumlah langkah ke depan yang diprediksi (default: 1)
        
        Returns:
            Tuple: (prediksi, alpha_optimal, info)
        """
        if len(data) < 2:
            raise ValueError("Data historis minimal 2 periode")
        
        if steps < 1:
            raise ValueError("Steps minimal 1")
        
        data_arr = np.array(data, dtype=float)
        
        # Build model
        model = HoltWinters(data_arr, trend=None, seasonal=None)
        
        # Fit model
        fit_kwargs = {'optimized': optimize}
        if alpha is not None:
            fit_kwargs['smoothing_level'] = float(alpha)
            fit_kwargs['optimized'] = False
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = model.fit(**fit_kwargs)
        
        alpha_opt = float(fit.params.get('smoothing_level', 0.5))
        
        # Forecast
        forecast_future = fit.forecast(steps)
        next_prediction = float(forecast_future[0])
        future_forecasts = [float(f) for f in forecast_future]
        
        # Fitted values (in-sample 1-step ahead forecasts)
        fitted = fit.fittedvalues
        forecast_values = [float(f) for f in fitted]
        
        info = {
            'alpha': alpha_opt,
            'forecast_values': forecast_values,
            'future_forecasts': future_forecasts,
            'steps': steps,
            'method': 'SES'
        }
        
        return float(next_prediction), alpha_opt, info


class DoubleExponentialSmoothing:
    """
    Double Exponential Smoothing (DES) / Holt's Method
    Cocok untuk data dengan trend tapi tanpa seasonality
    Menggunakan statsmodels untuk optimasi parameter MLE
    """
    
    @staticmethod
    def predict(data: List[float], alpha: Optional[float] = None,
                beta: Optional[float] = None, optimize: bool = True, 
                steps: int = 1) -> Tuple[float, float, float, dict]:
        """
        Melakukan prediksi menggunakan Double Exponential Smoothing
        
        Args:
            data: List data historis
            alpha: Parameter smoothing level (0-1)
            beta: Parameter smoothing trend (0-1)
            optimize: Jika True, akan mencari alpha dan beta optimal
            steps: Jumlah langkah ke depan yang diprediksi (default: 1)
        
        Returns:
            Tuple: (prediksi, alpha_optimal, beta_optimal, info)
        """
        if len(data) < 3:
            raise ValueError("Data historis minimal 3 periode untuk DES")
        
        if steps < 1:
            raise ValueError("Steps minimal 1")
        
        data_arr = np.array(data, dtype=float)
        
        # Build model with additive trend
        model = HoltWinters(data_arr, trend='add', seasonal=None)
        
        # Fit model
        fit_kwargs = {'optimized': optimize}
        if alpha is not None:
            fit_kwargs['smoothing_level'] = float(alpha)
        if beta is not None:
            fit_kwargs['smoothing_trend'] = float(beta)
        if alpha is not None and beta is not None:
            fit_kwargs['optimized'] = False
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = model.fit(**fit_kwargs)
        
        alpha_opt = float(fit.params.get('smoothing_level', 0.5))
        beta_opt = float(fit.params.get('smoothing_trend', 0.3))
        
        # Forecast
        forecast_future = fit.forecast(steps)
        next_prediction = float(forecast_future[0])
        future_forecasts = [float(f) for f in forecast_future]
        
        # Fitted values
        fitted = fit.fittedvalues
        forecast_values = [float(f) for f in fitted]
        
        # Extract level and trend
        level_values = [float(v) for v in fit.level]
        trend_values = [float(v) for v in fit.trend]
        
        info = {
            'alpha': alpha_opt,
            'beta': beta_opt,
            'level_values': level_values,
            'trend_values': trend_values,
            'forecast_values': forecast_values,
            'future_forecasts': future_forecasts,
            'steps': steps,
            'method': 'DES'
        }
        
        return float(next_prediction), alpha_opt, beta_opt, info


class TripleExponentialSmoothing:
    """
    Triple Exponential Smoothing (TES) / Holt-Winters Method
    Cocok untuk data dengan trend dan seasonality
    Menggunakan statsmodels dengan dukungan multiplicative seasonal
    """
    
    @staticmethod
    def predict(data: List[float], seasonal_periods: int = 12,
                alpha: Optional[float] = None, beta: Optional[float] = None,
                gamma: Optional[float] = None, optimize: bool = True, 
                steps: int = 1) -> Tuple[float, float, float, float, dict]:
        """
        Melakukan prediksi menggunakan Triple Exponential Smoothing
        
        Mencoba beberapa konfigurasi dan memilih yang terbaik:
        1. Additive trend + Multiplicative seasonal (biasa terbaik untuk data bertumbuh)
        2. Multiplicative trend + Multiplicative seasonal
        3. Additive trend + Additive seasonal
        
        Args:
            data: List data historis (minimal 2 * seasonal_periods)
            seasonal_periods: Periode musiman (default: 12 untuk data bulanan)
            alpha: Parameter smoothing level (0-1)
            beta: Parameter smoothing trend (0-1)
            gamma: Parameter smoothing seasonal (0-1)
            optimize: Jika True, akan mencari parameter optimal
            steps: Jumlah langkah ke depan yang diprediksi (default: 1)
        
        Returns:
            Tuple: (prediksi, alpha_optimal, beta_optimal, gamma_optimal, info)
        """
        if len(data) < 2 * seasonal_periods:
            raise ValueError(f"Data historis minimal {2 * seasonal_periods} periode untuk TES")
        
        if steps < 1:
            raise ValueError("Steps minimal 1")
        
        data_arr = np.array(data, dtype=float)
        
        # Konfigurasi yang akan dicoba (urutan prioritas)
        configs = [
            {'trend': 'add', 'seasonal': 'mul', 'name': 'add+mul'},
            {'trend': 'mul', 'seasonal': 'mul', 'name': 'mul+mul'},
            {'trend': 'add', 'seasonal': 'add', 'name': 'add+add'},
            {'trend': 'add', 'seasonal': 'mul', 'damped_trend': True, 'name': 'damped_add+mul'},
        ]
        
        # Jika alpha/beta/gamma diberikan manual, hanya gunakan 1 config
        if alpha is not None and beta is not None and gamma is not None:
            configs = [{'trend': 'add', 'seasonal': 'mul', 'name': 'manual'}]
        
        best_fit = None
        best_sse = float('inf')
        best_config_name = ''
        
        for config in configs:
            try:
                config_name = config.pop('name')
                model = HoltWinters(
                    data_arr, 
                    seasonal_periods=seasonal_periods,
                    **config
                )
                
                fit_kwargs = {'optimized': optimize}
                if alpha is not None:
                    fit_kwargs['smoothing_level'] = float(alpha)
                if beta is not None:
                    fit_kwargs['smoothing_trend'] = float(beta)
                if gamma is not None:
                    fit_kwargs['smoothing_seasonal'] = float(gamma)
                if alpha is not None and beta is not None and gamma is not None:
                    fit_kwargs['optimized'] = False
                
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    fit = model.fit(**fit_kwargs)
                
                # Hitung SSE (Sum of Squared Errors) untuk membandingkan konfigurasi
                fitted = fit.fittedvalues
                residuals = data_arr - fitted
                sse = float(np.sum(residuals[seasonal_periods:] ** 2))
                
                if sse < best_sse:
                    best_sse = sse
                    best_fit = fit
                    best_config_name = config_name
                    
                config['name'] = config_name
            except Exception:
                config['name'] = config.get('name', config_name)
                continue
        
        if best_fit is None:
            raise ValueError("Tidak dapat membangun model TES untuk data ini")
        
        fit = best_fit
        alpha_opt = float(fit.params.get('smoothing_level', 0.5))
        beta_opt = float(fit.params.get('smoothing_trend', 0.3))
        gamma_opt = float(fit.params.get('smoothing_seasonal', 0.2))
        
        # Forecast
        forecast_future = fit.forecast(steps)
        next_prediction = float(forecast_future[0])
        future_forecasts = [float(f) for f in forecast_future]
        
        # Ensure predictions are positive
        future_forecasts = [max(0.0, f) for f in future_forecasts]
        next_prediction = max(0.0, next_prediction)
        
        # Fitted values
        fitted = fit.fittedvalues
        forecast_values = [float(f) for f in fitted]
        
        # Extract components
        level_values = [float(v) for v in fit.level]
        trend_values = [float(v) for v in fit.trend]
        seasonal_values = [float(v) for v in fit.season]
        
        info = {
            'alpha': alpha_opt,
            'beta': beta_opt,
            'gamma': gamma_opt,
            'seasonal_periods': seasonal_periods,
            'level_values': level_values,
            'trend_values': trend_values,
            'seasonal_values': seasonal_values,
            'forecast_values': forecast_values,
            'future_forecasts': future_forecasts,
            'steps': steps,
            'method': 'TES',
            'best_config': best_config_name,
        }
        
        return float(next_prediction), alpha_opt, beta_opt, gamma_opt, info
