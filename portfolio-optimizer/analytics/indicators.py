import numpy as np
import pandas as pd

# Individual Stock Indicators

def calculate_expected_return(prices: pd.Series) -> float:
    returns = prices.pct_change().dropna()
    return (1 + returns.mean())**252 - 1

def calculate_volatility(prices: pd.Series) -> float:
    """Computes standard deviation of daily returns."""
    returns = prices.pct_change().dropna()
    return returns.std()

def calculate_sharpe_ratio(prices: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Computes Sharpe ratio assuming 252 trading days."""
    daily_returns = prices.pct_change().dropna()
    excess_returns = daily_returns - (risk_free_rate / 252)
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

def calculate_max_drawdown(prices: pd.Series) -> float:
    """Computes the maximum drawdown."""
    cumulative_max = prices.cummax()
    drawdowns = (prices - cumulative_max) / cumulative_max
    return drawdowns.min()

def calculate_var(prices: pd.Series, confidence_level: float = 0.95) -> float:
    """Computes Value at Risk (VaR) using historical simulation."""
    returns = prices.pct_change().dropna()
    return np.percentile(returns, (1 - confidence_level) * 100)

# Portfolio-Level Calculations

def weighted_average(values: list, weights: list) -> float:
    return np.average(values, weights=weights)

def calculate_portfolio_expected_return(expected_returns: list, weights: list) -> float:
    return weighted_average(expected_returns, weights)

def calculate_portfolio_volatility(cov_matrix: np.ndarray, weights: np.ndarray) -> float:
    return np.sqrt(weights.T @ cov_matrix @ weights)

def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """Computes beta as cov(Rs, Rm) / var(Rm)"""
    return np.cov(stock_returns, market_returns)[0, 1] / np.var(market_returns)

def calculate_alpha(stock_returns: pd.Series, market_returns: pd.Series, beta: float, risk_free_rate: float = 0.02) -> float:
    daily_alpha = stock_returns.mean() - (risk_free_rate / 252 + beta * (market_returns.mean() - risk_free_rate / 252))
    return (1 + daily_alpha)**252 - 1

def calculate_diversification_score(corr_matrix: pd.DataFrame) -> float:
    """Lower average correlation implies higher diversification."""
    n = len(corr_matrix)
    mask = ~np.eye(n, dtype=bool)
    avg_corr = corr_matrix.where(mask).stack().mean()
    return 1 - avg_corr  # Higher is better
