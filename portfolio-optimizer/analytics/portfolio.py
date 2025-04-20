import numpy as np
import pandas as pd
from analytics.data import (
    fetch_daily_adjusted,
    fetch_multiple_series,
    calculate_daily_returns,
    calculate_log_returns,
    align_price_series,
)
from analytics.indicators import (
    calculate_portfolio_expected_return,
    calculate_portfolio_volatility,
    calculate_sharpe_ratio,
    calculate_diversification_score,
    calculate_max_drawdown,
    calculate_var,
    calculate_beta,
    calculate_alpha,
)

# In-memory cache for SPY
_market_cache = {}

def get_market_series(symbol="SPY"):
    if symbol not in _market_cache:
        _market_cache[symbol] = fetch_daily_adjusted(symbol)
    return _market_cache[symbol]

def compute_portfolio_metrics(price_df: pd.DataFrame, weights: np.ndarray, risk_free_rate: float = 0.02) -> dict:
    """
    Computes expected return, volatility, Sharpe ratio, drawdown, VaR,
    diversification score, beta, and alpha for the whole portfolio.
    Assumes price_df columns = tickers, rows = dates, values = adjusted close prices.
    """
    daily_returns = price_df.pct_change().dropna()

    # Core metrics
    expected_returns = daily_returns.mean()
    cov_matrix = daily_returns.cov()

    portfolio_return = calculate_portfolio_expected_return(expected_returns, weights)
    portfolio_volatility = calculate_portfolio_volatility(cov_matrix.values, weights)
    sharpe_ratio = calculate_sharpe_ratio((price_df @ weights), risk_free_rate)

    # Diversification score
    corr_matrix = daily_returns.corr()
    diversification_score = calculate_diversification_score(corr_matrix)

    # Portfolio price series to compute drawdown & VaR
    portfolio_prices = (price_df * weights).sum(axis=1)
    max_drawdown = calculate_max_drawdown(portfolio_prices)
    value_at_risk = calculate_var(portfolio_prices)

    # Beta and Alpha vs SPY (market proxy)
    try:
        market_series = get_market_series()
        aligned = pd.concat([portfolio_prices.pct_change(), market_series.pct_change()], axis=1).dropna()
        aligned.columns = ["portfolio", "market"]
        beta = calculate_beta(aligned["portfolio"], aligned["market"])
        alpha = calculate_alpha(aligned["portfolio"], aligned["market"], beta, risk_free_rate)
    except Exception as e:
        print(f"Failed to calculate alpha/beta: {e}")
        beta = None
        alpha = None

    return {
        "expected_return": portfolio_return,
        "volatility": portfolio_volatility,
        "sharpe_ratio": sharpe_ratio,
        "diversification_score": diversification_score,
        "max_drawdown": max_drawdown,
        "value_at_risk": value_at_risk,
        "beta": beta,
        "alpha": alpha
    }

def compute_correlation_matrix(price_df: pd.DataFrame) -> pd.DataFrame:
    """Computes correlation matrix of asset returns."""
    return price_df.pct_change().dropna().corr()
