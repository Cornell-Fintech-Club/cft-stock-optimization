import psycopg2
import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
# Your Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Database connection details
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

# Fetch OHLC data from Alpha Vantage API
def fetch_ohlc_data(ticker, date):
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": "5min",  # You can adjust this as needed (1min, 15min, etc.)
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    # print("Key Debug",ALPHA_VANTAGE_API_KEY)

    response = requests.get(url, params=params)
    data = response.json()

    # print("API response:", data)


    return data['Time Series (5min)']  # Adjust this if you want a different time series

# Insert data into TimescaleDB
def insert_ohlc_data(data, ticker):
    for timestamp, candle in data.items():
        timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")  # Convert timestamp to datetime
        cur.execute(
            """
            INSERT INTO ohlc_data (ticker, timestamp, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (ticker, timestamp, candle['1. open'], candle['2. high'], candle['3. low'], candle['4. close'], candle['5. volume'])
        )
    conn.commit()

# Fetch and insert today's data for AAPL
date_today = datetime.date.today().isoformat()
ohlc_data = fetch_ohlc_data("AAPL", date_today)
insert_ohlc_data(ohlc_data, "AAPL")

print("Data inserted successfully!")

# Close connection
cur.close()
conn.close()
