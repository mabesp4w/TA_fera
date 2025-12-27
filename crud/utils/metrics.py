"""
Utility functions untuk menghitung metrik evaluasi prediksi
"""
from decimal import Decimal
from typing import List
import numpy as np


def calculate_mape(actual: List[float], predicted: List[float]) -> float:
    """
    Menghitung Mean Absolute Percentage Error (MAPE)
    
    Args:
        actual: List nilai aktual
        predicted: List nilai prediksi
    
    Returns:
        MAPE dalam persen
    """
    if len(actual) != len(predicted):
        raise ValueError("Panjang actual dan predicted harus sama")
    
    if len(actual) == 0:
        return 0.0
    
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    # Hindari division by zero
    mask = actual != 0
    if not mask.any():
        return 0.0
    
    percentage_errors = np.abs((actual[mask] - predicted[mask]) / actual[mask]) * 100
    mape = np.mean(percentage_errors)
    
    return float(mape)


def calculate_mae(actual: List[float], predicted: List[float]) -> float:
    """
    Menghitung Mean Absolute Error (MAE)
    
    Args:
        actual: List nilai aktual
        predicted: List nilai prediksi
    
    Returns:
        MAE
    """
    if len(actual) != len(predicted):
        raise ValueError("Panjang actual dan predicted harus sama")
    
    if len(actual) == 0:
        return 0.0
    
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    mae = np.mean(np.abs(actual - predicted))
    
    return float(mae)


def calculate_rmse(actual: List[float], predicted: List[float]) -> float:
    """
    Menghitung Root Mean Squared Error (RMSE)
    
    Args:
        actual: List nilai aktual
        predicted: List nilai prediksi
    
    Returns:
        RMSE
    """
    if len(actual) != len(predicted):
        raise ValueError("Panjang actual dan predicted harus sama")
    
    if len(actual) == 0:
        return 0.0
    
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    mse = np.mean((actual - predicted) ** 2)
    rmse = np.sqrt(mse)
    
    return float(rmse)


def calculate_all_metrics(actual: List[float], predicted: List[float]) -> dict:
    """
    Menghitung semua metrik evaluasi sekaligus
    
    Args:
        actual: List nilai aktual
        predicted: List nilai prediksi
    
    Returns:
        Dictionary berisi MAPE, MAE, RMSE
    """
    return {
        'mape': calculate_mape(actual, predicted),
        'mae': calculate_mae(actual, predicted),
        'rmse': calculate_rmse(actual, predicted)
    }

