import numpy as np
import pandas as pd
import yfinance as yf

# Data Fetching from yfinance
def fetch_daily_adjusted(symbol: str) -> pd.Series:
    """Fetch daily close prices for a single symbol using yfinance."""
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if df.empty or "Close" not in df.columns:
        raise ValueError(f"No valid 'Close' data found for {symbol}")
    return df["Close"].dropna()

def fetch_multiple_series(symbols: list) -> dict:
    """Fetch close prices for multiple symbols using yfinance."""
    df = yf.download(symbols, period="6mo", interval="1d", progress=False)
    result = {}

    if isinstance(df.columns, pd.MultiIndex):
        for symbol in symbols:
            try:
                result[symbol] = df["Close"][symbol].dropna()
            except Exception as e:
                raise ValueError(f"Missing data for {symbol}: {e}")
    else:
        symbol = symbols[0]
        if "Close" not in df.columns:
            raise ValueError(f"'Close' column not found for {symbol}")
        result[symbol] = df["Close"].dropna()

    return result

def calculate_daily_returns(price_series: pd.Series) -> pd.Series:
    return price_series.pct_change().dropna()

def calculate_log_returns(price_series: pd.Series) -> pd.Series:
    return np.log(price_series / price_series.shift(1)).dropna()

def align_price_series(price_dict: dict) -> pd.DataFrame:
    """Aligns multiple price series into a DataFrame with shared dates."""
    return pd.DataFrame(price_dict).dropna()