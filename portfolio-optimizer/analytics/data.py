import numpy as np
import pandas as pd
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# ----------------------------
# Data Fetching and Utilities
# ----------------------------

def fetch_daily_adjusted(symbol: str) -> pd.Series:
    """Fetch daily close prices for a given stock symbol (free-tier safe)."""
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "outputsize": "compact"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    try:
        time_series = data["Time Series (Daily)"]
    except KeyError:
        raise ValueError(f"API response error for symbol {symbol}: {data}")

    price_data = {
        datetime.strptime(date, "%Y-%m-%d"): float(values["4. close"])
        for date, values in time_series.items()
    }
    return pd.Series(price_data).sort_index()

def fetch_multiple_series(symbols: list) -> dict:
    """Fetch close price series for multiple symbols."""
    return {symbol: fetch_daily_adjusted(symbol) for symbol in symbols}

def calculate_daily_returns(price_series: pd.Series) -> pd.Series:
    return price_series.pct_change().dropna()

def calculate_log_returns(price_series: pd.Series) -> pd.Series:
    return np.log(price_series / price_series.shift(1)).dropna()

def align_price_series(price_dict: dict) -> pd.DataFrame:
    """Aligns multiple price series into a DataFrame with shared dates."""
    return pd.DataFrame(price_dict).dropna()
