import yfinance as yf
from datetime import datetime
from app import db
from app.models import OHLCData
import pandas as pd


def fetch_and_store_data(ticker, start_date=None, end_date=None):
    # can change date and range entries 
    period = "6mo"
    interval = "1d"
    df = yf.download(ticker, period=period, interval=interval, start=start_date, end=end_date, progress=False)

    if df.empty:
        print(f"Error: No data found for {ticker}")
        return

    new_entries = []
    df = df.reset_index()

    for _, row in df.iterrows():
        timestamp = pd.to_datetime(row["Date"])
        if isinstance(timestamp, pd.Series):
            timestamp = timestamp.iloc[0]

        open_price = float(row["Open"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        close_price = float(row["Close"])
        volume = int(row["Volume"])

        existing_record = OHLCData.query.filter_by(ticker=ticker, timestamp=timestamp).first()
        if existing_record:
            print(f"Data for {ticker} on {timestamp.date()} already exists. Skipping.")
            continue

        new_entries.append(
            OHLCData(
                ticker=ticker,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                #Temp fill-in
                sector='None'
            )
        )

    if new_entries:
        db.session.bulk_save_objects(new_entries)
        db.session.commit()
        print(f"Successfully added {len(new_entries)} new records for {ticker}")
    else:
        print(f"No new records added for {ticker}")
