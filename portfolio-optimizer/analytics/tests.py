import numpy as np
import pandas as pd
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from data import (
    fetch_daily_adjusted,
    fetch_multiple_series,
    calculate_daily_returns,
    calculate_log_returns,
    align_price_series,
)
from portfolio import (
    compute_portfolio_metrics,
    compute_correlation_matrix,
)

load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

#Testing script

if __name__ == "__main__":
    # print(ALPHA_VANTAGE_API_KEY)
    test_symbols = ["AAPL", "MSFT", "JPM", "XOM", "JNJ"]
    try:
        print("Fetching price data...")
        price_dict = fetch_multiple_series(test_symbols)
        aligned_prices = align_price_series(price_dict)

        # Equal weights for simplicity
        weights = np.ones(len(test_symbols)) / len(test_symbols)

        print("\nSample price data:")
        print(aligned_prices.head())

        print("\nComputing portfolio metrics...")
        results = compute_portfolio_metrics(aligned_prices, weights)
        for key, value in results.items():
            print(f"{key}: {value:.4f}")

        print("\nCorrelation matrix:")
        print(compute_correlation_matrix(aligned_prices))

    except Exception as e:
        print(f"Error during test run: {e}")
