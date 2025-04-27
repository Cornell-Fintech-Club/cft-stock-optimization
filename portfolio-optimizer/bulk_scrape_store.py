import time
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text
from analytics.sector_scraper import scrape_top_100_tickers
from analytics.sector_scraper import SECTOR_FILTERS

DB_URL = "postgresql://gregoryparent:your_password@localhost/portfolio_optimizer"
engine = create_engine(DB_URL)


#Download OHLC for a single ticker
def fetch_ohlc_for_ticker(ticker: str) -> pd.DataFrame:
    yf_ticker = yf.Ticker(ticker)
    df = yf_ticker.history(period="1y", interval="1d", auto_adjust=False)

    if df.empty:
        return pd.DataFrame()

    df = df.reset_index()
    df["ticker"] = ticker

    return df[["ticker", "Date", "Open", "High", "Low", "Close", "Volume"]]


def store_dataframe(df: pd.DataFrame, sector: str):
    if df.empty:
        return

    df.columns = [col.lower() if isinstance(col, str) else str(col) for col in df.columns]
    df = df.rename(columns={"date": "timestamp"})
    
    df["sector"] = sector

    df = df[["ticker", "timestamp", "open", "high", "low", "close", "volume", "sector"]]

    df.to_sql("ohlc_data", engine, if_exists="append", index=False, method="multi")

    df["sector"] = sector
    df.to_sql("ohlc_data", engine, if_exists="append", index=False, method="multi")


def bulk_scrape_and_store():

    with engine.connect() as conn:
        print("Clearing existing OHLC data...")
        conn.execute(text("TRUNCATE TABLE ohlc_data RESTART IDENTITY;"))
        conn.commit()
    for sector in SECTOR_FILTERS:
        print(f"\nProcessing sector: {sector}")
        tickers = scrape_top_100_tickers(sector)
        print(f"Scraped {len(tickers)} tickers for {sector}")

        for i, ticker in enumerate(tickers):
            try:
                df = fetch_ohlc_for_ticker(ticker)
                if not df.empty:
                    store_dataframe(df, sector)
                    print(f"{i+1:03}: Inserted {len(df)} rows for {ticker}")
                else:
                    print(f"{i+1:03}: No data for {ticker}")
            except Exception as e:
                print(f"{i+1:03}: Error for {ticker}: {e}")
            time.sleep(1)  

#smaller testing method
def bulk_scrape_and_store_tech():
    sector = "technology"
    print(f"\n📊 Processing sector: {sector}")
    tickers = scrape_top_100_tickers(sector)
    print(f"Scraped {len(tickers)} tickers for {sector}")

    for i, ticker in enumerate(tickers):
        try:
            df = fetch_ohlc_for_ticker(ticker)
            if not df.empty:
                store_dataframe(df, sector)
                print(f"{i+1:03}: Inserted {len(df)} rows for {ticker}")
            else:
                print(f"{i+1:03}: No data for {ticker}")
        except Exception as e:
            print(f"{i+1:03}: Error for {ticker}: {e}")
        time.sleep(1)  

if __name__ == "__main__":
    bulk_scrape_and_store()