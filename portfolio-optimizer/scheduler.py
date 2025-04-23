from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import yfinance as yf
import pandas as pd
import time

from analytics.sector_scraper import SECTOR_FILTERS, scrape_top_100_tickers

DB_URL = "postgresql://gregoryparent:your_password@localhost/portfolio_optimizer"
engine = create_engine(DB_URL)


def fetch_today_ohlc(ticker: str) -> pd.DataFrame:
    today = datetime.today()
    yesterday = today - timedelta(days=5)  # cover buffer in case markets closed
    df = yf.Ticker(ticker).history(start=yesterday.strftime("%Y-%m-%d"), interval="1d", auto_adjust=False)
    
    if df.empty:
        return pd.DataFrame()

    df = df.reset_index()
    df["ticker"] = ticker
    df = df.rename(columns={"Date": "timestamp"})
    df = df[["ticker", "timestamp", "Open", "High", "Low", "Close", "Volume"]]
    df.columns = df.columns.str.lower()

    return df


def update_latest_data():
    print(f"\nJob started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for sector in SECTOR_FILTERS:
        tickers = scrape_top_100_tickers(sector)
        print(f"{sector}: {len(tickers)} tickers")

        for ticker in tickers:
            try:
                df = fetch_today_ohlc(ticker)
                if df.empty:
                    continue
                df["sector"] = sector
                df.to_sql("ohlc_data", engine, if_exists="append", index=False)
                print(f"{ticker}: {len(df)} rows inserted")
            except Exception as e:
                print(f"{ticker}: {e}")
            time.sleep(0.3)


#Scheduler Setup
scheduler = BackgroundScheduler()
scheduler.add_job(update_latest_data, "interval", hours=1)
scheduler.start()

print("Scheduler started. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(60)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    print("Scheduler stopped.")
