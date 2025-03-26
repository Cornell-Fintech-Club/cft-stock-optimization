import requests
from datetime import datetime
from app import db
from app.models import OHLCData
import os

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
BASE_URL = "https://www.alphavantage.co/query"

def fetch_and_store_data(ticker):
    url = f"{BASE_URL}?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    # print(data)
    
    # Check if data exists and handle missing data gracefully
    if "Time Series (Daily)" not in data:
        print(f"Error: No data found for {ticker}")
        return
    
    time_series = data["Time Series (Daily)"]
    
    for date, values in time_series.items():
        timestamp = datetime.strptime(date, "%Y-%m-%d")
        open_price = float(values["1. open"])
        high_price = float(values["2. high"])
        low_price = float(values["3. low"])
        close_price = float(values["4. close"])
        volume = int(values["5. volume"])
        
        # Check if the data for the given date already exists in the database
        existing_record = OHLCData.query.filter_by(ticker=ticker, timestamp=timestamp).first()
        if existing_record:
            print(f"Data for {ticker} on {date} already exists. Skipping.")
        else:
            # Save data to the database
            ohlc_data = OHLCData(ticker=ticker, timestamp=timestamp, open=open_price, high=high_price, low=low_price, close=close_price, volume=volume)
            db.session.add(ohlc_data)
    
    # Commit the transaction to save data
    db.session.commit()
