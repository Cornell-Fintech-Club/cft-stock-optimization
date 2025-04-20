import psycopg2
import datetime
import os
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "dbname": "portfolio_optimizer",
    "user": "gregoryparent",
    "password": os.getenv("DB_PASSWORD"),
    "host": "localhost",
    "port": "5432"
}

# Connect to PostgreSQL
conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

# Fetch OHLC data using yfinance

def fetch_ohlc_data(ticker):
    df = yf.download(ticker, period="1d", interval="5m", progress=False)
    if df.empty:
        raise ValueError(f"No intraday data found for {ticker}")
    df = df.reset_index()
    return df

# Insert data into TimescaleDB

def insert_ohlc_data(df, ticker):
    for _, row in df.iterrows():
        timestamp = row["Datetime"]
        cur.execute(
            """
            INSERT INTO ohlc_data (ticker, timestamp, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (
                ticker,
                timestamp,
                row["Open"],
                row["High"],
                row["Low"],
                row["Close"],
                row["Volume"]
            )
        )
    conn.commit()

# Example usage
# df = fetch_ohlc_data("AAPL")
# insert_ohlc_data(df, "AAPL")

print("Data inserted successfully!")

# Close connection
cur.close()
conn.close()
