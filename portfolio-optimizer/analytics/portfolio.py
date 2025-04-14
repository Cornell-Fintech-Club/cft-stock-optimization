import numpy as np
import pandas as pd
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
from data import (
    fetch_daily_adjusted,
    fetch_multiple_series,
    calculate_daily_returns,
    calculate_log_returns,
    align_price_series,
)


BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def compute_portfolio_metrics(price_df: pd.DataFrame, weights: np.ndarray, risk_free_rate: float = 0.02) -> dict:
    """
    Computes expected return, volatility, Sharpe ratio for the whole portfolio.
    Assumes price_df columns = tickers, rows = dates, values = adjusted close prices.
    """
    # Calculate daily returns for each stock
    daily_returns = price_df.pct_change().dropna()

    # Expected return = weighted average of mean daily returns
    expected_returns = daily_returns.mean()
    portfolio_return = np.dot(weights, expected_returns)

    # Covariance matrix and portfolio volatility
    cov_matrix = daily_returns.cov()
    portfolio_volatility = np.sqrt(weights.T @ cov_matrix.values @ weights)

    # Sharpe ratio
    sharpe_ratio = (portfolio_return - (risk_free_rate / 252)) / portfolio_volatility * np.sqrt(252)

    return {
        "expected_return": portfolio_return,
        "volatility": portfolio_volatility,
        "sharpe_ratio": sharpe_ratio,
    }

def compute_correlation_matrix(price_df: pd.DataFrame) -> pd.DataFrame:
    """Computes correlation matrix of asset returns."""
    return price_df.pct_change().dropna().corr()
