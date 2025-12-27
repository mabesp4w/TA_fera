"""
Implementasi algoritma Exponential Smoothing untuk prediksi
- Simple Exponential Smoothing (SES)
- Double Exponential Smoothing (DES/Holt)
- Triple Exponential Smoothing (TES/Holt-Winters)
"""
import numpy as np
from typing import List, Tuple, Optional
from decimal import Decimal
from scipy.optimize import minimize


class SimpleExponentialSmoothing:
    """
    Simple Exponential Smoothing (SES)
    Cocok untuk data tanpa trend dan seasonality
    """
    
    @staticmethod
    def predict(data: List[float], alpha: Optional[float] = None, 
                optimize: bool = True) -> Tuple[float, float, dict]:
        """
        Melakukan prediksi menggunakan Simple Exponential Smoothing
        
        Args:
            data: List data historis
            alpha: Parameter smoothing (0-1), jika None akan dioptimasi
            optimize: Jika True, akan mencari alpha optimal
        
        Returns:
            Tuple: (prediksi, alpha_optimal, info)
        """
        if len(data) < 2:
            raise ValueError("Data historis minimal 2 periode")
        
        data = np.array(data, dtype=float)
        
        # Optimasi alpha jika diperlukan
        if optimize or alpha is None:
            alpha_opt = SimpleExponentialSmoothing._optimize_alpha(data)
        else:
            alpha_opt = float(alpha)
            if not 0 <= alpha_opt <= 1:
                raise ValueError("Alpha harus antara 0 dan 1")
        
        # Hitung prediksi
        # Formula: F(t+1) = alpha * Y(t) + (1-alpha) * F(t)
        # Initial: F(1) = Y(1)
        forecast = np.zeros(len(data))
        forecast[0] = data[0]
        
        for i in range(1, len(data)):
            forecast[i] = alpha_opt * data[i-1] + (1 - alpha_opt) * forecast[i-1]
        
        # Prediksi untuk periode berikutnya
        next_prediction = alpha_opt * data[-1] + (1 - alpha_opt) * forecast[-1]
        
        info = {
            'alpha': alpha_opt,
            'forecast_values': forecast.tolist(),
            'method': 'SES'
        }
        
        return float(next_prediction), alpha_opt, info
    
    @staticmethod
    def _optimize_alpha(data: np.ndarray) -> float:
        """
        Optimasi parameter alpha dengan meminimalkan SSE
        """
        def sse(alpha):
            if not 0 <= alpha <= 1:
                return np.inf
            
            forecast = np.zeros(len(data))
            forecast[0] = data[0]
            
            for i in range(1, len(data)):
                forecast[i] = alpha * data[i-1] + (1 - alpha) * forecast[i-1]
            
            return np.sum((data - forecast) ** 2)
        
        result = minimize(sse, x0=0.5, bounds=[(0, 1)], method='L-BFGS-B')
        return float(result.x[0])


class DoubleExponentialSmoothing:
    """
    Double Exponential Smoothing (DES) / Holt's Method
    Cocok untuk data dengan trend tapi tanpa seasonality
    """
    
    @staticmethod
    def predict(data: List[float], alpha: Optional[float] = None,
                beta: Optional[float] = None, optimize: bool = True) -> Tuple[float, float, float, dict]:
        """
        Melakukan prediksi menggunakan Double Exponential Smoothing
        
        Args:
            data: List data historis
            alpha: Parameter smoothing level (0-1)
            beta: Parameter smoothing trend (0-1)
            optimize: Jika True, akan mencari alpha dan beta optimal
        
        Returns:
            Tuple: (prediksi, alpha_optimal, beta_optimal, info)
        """
        if len(data) < 3:
            raise ValueError("Data historis minimal 3 periode untuk DES")
        
        data = np.array(data, dtype=float)
        
        # Optimasi parameter jika diperlukan
        if optimize or alpha is None or beta is None:
            alpha_opt, beta_opt = DoubleExponentialSmoothing._optimize_params(data)
        else:
            alpha_opt = float(alpha)
            beta_opt = float(beta)
            if not (0 <= alpha_opt <= 1 and 0 <= beta_opt <= 1):
                raise ValueError("Alpha dan beta harus antara 0 dan 1")
        
        # Hitung level dan trend
        level = np.zeros(len(data))
        trend = np.zeros(len(data))
        
        # Initial values
        level[0] = data[0]
        trend[0] = data[1] - data[0] if len(data) > 1 else 0
        
        # Update level dan trend
        for i in range(1, len(data)):
            level[i] = alpha_opt * data[i] + (1 - alpha_opt) * (level[i-1] + trend[i-1])
            trend[i] = beta_opt * (level[i] - level[i-1]) + (1 - beta_opt) * trend[i-1]
        
        # Prediksi untuk periode berikutnya
        next_prediction = level[-1] + trend[-1]
        
        info = {
            'alpha': alpha_opt,
            'beta': beta_opt,
            'level_values': level.tolist(),
            'trend_values': trend.tolist(),
            'method': 'DES'
        }
        
        return float(next_prediction), alpha_opt, beta_opt, info
    
    @staticmethod
    def _optimize_params(data: np.ndarray) -> Tuple[float, float]:
        """
        Optimasi parameter alpha dan beta
        """
        def sse(params):
            alpha, beta = params
            if not (0 <= alpha <= 1 and 0 <= beta <= 1):
                return np.inf
            
            level = np.zeros(len(data))
            trend = np.zeros(len(data))
            level[0] = data[0]
            trend[0] = data[1] - data[0] if len(data) > 1 else 0
            
            for i in range(1, len(data)):
                level[i] = alpha * data[i] + (1 - alpha) * (level[i-1] + trend[i-1])
                trend[i] = beta * (level[i] - level[i-1]) + (1 - beta) * trend[i-1]
            
            forecast = level[:-1] + trend[:-1]
            return np.sum((data[1:] - forecast) ** 2)
        
        result = minimize(sse, x0=[0.5, 0.5], bounds=[(0, 1), (0, 1)], method='L-BFGS-B')
        return float(result.x[0]), float(result.x[1])


class TripleExponentialSmoothing:
    """
    Triple Exponential Smoothing (TES) / Holt-Winters Method
    Cocok untuk data dengan trend dan seasonality
    """
    
    @staticmethod
    def predict(data: List[float], seasonal_periods: int = 12,
                alpha: Optional[float] = None, beta: Optional[float] = None,
                gamma: Optional[float] = None, optimize: bool = True) -> Tuple[float, float, float, float, dict]:
        """
        Melakukan prediksi menggunakan Triple Exponential Smoothing
        
        Args:
            data: List data historis (minimal 2 * seasonal_periods)
            seasonal_periods: Periode musiman (default: 12 untuk data bulanan)
            alpha: Parameter smoothing level (0-1)
            beta: Parameter smoothing trend (0-1)
            gamma: Parameter smoothing seasonal (0-1)
            optimize: Jika True, akan mencari parameter optimal
        
        Returns:
            Tuple: (prediksi, alpha_optimal, beta_optimal, gamma_optimal, info)
        """
        if len(data) < 2 * seasonal_periods:
            raise ValueError(f"Data historis minimal {2 * seasonal_periods} periode untuk TES")
        
        data = np.array(data, dtype=float)
        
        # Optimasi parameter jika diperlukan
        if optimize or alpha is None or beta is None or gamma is None:
            alpha_opt, beta_opt, gamma_opt = TripleExponentialSmoothing._optimize_params(
                data, seasonal_periods
            )
        else:
            alpha_opt = float(alpha)
            beta_opt = float(beta)
            gamma_opt = float(gamma)
            if not (0 <= alpha_opt <= 1 and 0 <= beta_opt <= 1 and 0 <= gamma_opt <= 1):
                raise ValueError("Alpha, beta, dan gamma harus antara 0 dan 1")
        
        # Hitung level, trend, dan seasonal
        level = np.zeros(len(data))
        trend = np.zeros(len(data))
        seasonal = np.zeros(len(data))
        
        # Initial seasonal values (rata-rata untuk setiap periode musiman)
        seasonal_avg = np.zeros(seasonal_periods)
        for i in range(seasonal_periods):
            seasonal_avg[i] = np.mean([data[j] for j in range(i, len(data), seasonal_periods)])
        
        # Normalize seasonal
        seasonal_avg = seasonal_avg / np.mean(seasonal_avg)
        
        # Initial values
        level[0] = data[0] / seasonal_avg[0]
        trend[0] = (data[1] / seasonal_avg[1] - data[0] / seasonal_avg[0]) if len(data) > 1 else 0
        
        # Update level, trend, dan seasonal
        for i in range(len(data)):
            if i == 0:
                seasonal[i] = seasonal_avg[i % seasonal_periods]
            else:
                m = i % seasonal_periods
                if i < seasonal_periods:
                    level[i] = alpha_opt * (data[i] / seasonal_avg[m]) + (1 - alpha_opt) * (level[i-1] + trend[i-1])
                else:
                    level[i] = alpha_opt * (data[i] / seasonal[i-seasonal_periods]) + (1 - alpha_opt) * (level[i-1] + trend[i-1])
                
                trend[i] = beta_opt * (level[i] - level[i-1]) + (1 - beta_opt) * trend[i-1]
                
                if i >= seasonal_periods:
                    seasonal[i] = gamma_opt * (data[i] / level[i]) + (1 - gamma_opt) * seasonal[i-seasonal_periods]
                else:
                    seasonal[i] = seasonal_avg[m]
        
        # Prediksi untuk periode berikutnya
        h = 1  # horizon prediksi
        m = (len(data) + h - 1) % seasonal_periods
        next_prediction = (level[-1] + h * trend[-1]) * seasonal[-seasonal_periods + m]
        
        info = {
            'alpha': alpha_opt,
            'beta': beta_opt,
            'gamma': gamma_opt,
            'seasonal_periods': seasonal_periods,
            'level_values': level.tolist(),
            'trend_values': trend.tolist(),
            'seasonal_values': seasonal.tolist(),
            'method': 'TES'
        }
        
        return float(next_prediction), alpha_opt, beta_opt, gamma_opt, info
    
    @staticmethod
    def _optimize_params(data: np.ndarray, seasonal_periods: int) -> Tuple[float, float, float]:
        """
        Optimasi parameter alpha, beta, dan gamma
        """
        def sse(params):
            alpha, beta, gamma = params
            if not (0 <= alpha <= 1 and 0 <= beta <= 1 and 0 <= gamma <= 1):
                return np.inf
            
            try:
                level = np.zeros(len(data))
                trend = np.zeros(len(data))
                seasonal = np.zeros(len(data))
                
                # Initial seasonal
                seasonal_avg = np.zeros(seasonal_periods)
                for i in range(seasonal_periods):
                    seasonal_avg[i] = np.mean([data[j] for j in range(i, len(data), seasonal_periods)])
                seasonal_avg = seasonal_avg / np.mean(seasonal_avg)
                
                level[0] = data[0] / seasonal_avg[0]
                trend[0] = (data[1] / seasonal_avg[1] - data[0] / seasonal_avg[0]) if len(data) > 1 else 0
                
                for i in range(len(data)):
                    m = i % seasonal_periods
                    if i == 0:
                        seasonal[i] = seasonal_avg[m]
                    else:
                        if i < seasonal_periods:
                            level[i] = alpha * (data[i] / seasonal_avg[m]) + (1 - alpha) * (level[i-1] + trend[i-1])
                        else:
                            level[i] = alpha * (data[i] / seasonal[i-seasonal_periods]) + (1 - alpha) * (level[i-1] + trend[i-1])
                        
                        trend[i] = beta * (level[i] - level[i-1]) + (1 - beta) * trend[i-1]
                        
                        if i >= seasonal_periods:
                            seasonal[i] = gamma * (data[i] / level[i]) + (1 - gamma) * seasonal[i-seasonal_periods]
                        else:
                            seasonal[i] = seasonal_avg[m]
                
                # Calculate forecast and SSE
                forecast = np.zeros(len(data))
                for i in range(len(data)):
                    m = i % seasonal_periods
                    if i < seasonal_periods:
                        forecast[i] = level[i] * seasonal_avg[m]
                    else:
                        forecast[i] = (level[i-seasonal_periods] + trend[i-seasonal_periods]) * seasonal[i-seasonal_periods]
                
                return np.sum((data - forecast) ** 2)
            except:
                return np.inf
        
        result = minimize(sse, x0=[0.5, 0.5, 0.5], bounds=[(0, 1), (0, 1), (0, 1)], method='L-BFGS-B')
        return float(result.x[0]), float(result.x[1]), float(result.x[2])

