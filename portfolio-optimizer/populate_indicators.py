from app import create_app, db
from app.models import OHLCData, StockIndicator
from analytics.indicators import (
    calculate_expected_return,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_var,
    calculate_beta,
    calculate_alpha,
)
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import text
from app.scraper import fetch_and_store_data

app = create_app()

# def to_native(value):
#     """Convert NumPy numbers to native Python, leave others untouched."""
#     if value is None:
#         return None
#     # NumPy float / int
#     if hasattr(value, "item"):
#         try:
#             return value.item()
#         except Exception:
#             pass
#     return value

def fetch_close_prices_and_sector(ticker):
    records = (
        OHLCData.query.filter_by(ticker=ticker)
        .order_by(OHLCData.timestamp.asc())
        .all()
    )
    if not records:
        return None, None

    close_prices = pd.Series({r.timestamp: r.close for r in records})
    sector = records[0].sector
    return close_prices, sector

def fetch_market_prices():
    spy_records = (
        OHLCData.query.filter_by(ticker="SPY")
        .order_by(OHLCData.timestamp.asc())
        .all()
    )
    if not spy_records:
        print("SPY data not found in database. Fetching now...")
        fetch_and_store_data("SPY")
        db.session.commit()
        spy_records = (
            OHLCData.query.filter_by(ticker="SPY")
            .order_by(OHLCData.timestamp.asc())
            .all()
        )
    if not spy_records:
        print("Failed to retrieve SPY data after fetch attempt.")
        return None
    return pd.Series({r.timestamp: r.close for r in spy_records})

def populate_stock_indicators():
    with app.app_context():
        print("Clearing existing stock_indicators table...")
        db.session.execute(text('TRUNCATE TABLE stock_indicators;'))
        db.session.commit()

        tickers = [t[0] for t in db.session.query(OHLCData.ticker).distinct().all()]
        print(f"Found {len(tickers)} tickers. Calculating indicators...")

        market_prices = fetch_market_prices()

        for ticker in tickers:
            prices, sector = fetch_close_prices_and_sector(ticker)
            if prices is None or len(prices) < 2 or sector is None:
                print(f"Skipping {ticker} due to insufficient data or missing sector.")
                continue

            try:
                # compute raw indicators (may be NumPy types)
                exp_ret = calculate_expected_return(prices)
                vol      = calculate_volatility(prices)
                sr       = calculate_sharpe_ratio(prices)
                mdd      = calculate_max_drawdown(prices)
                var      = calculate_var(prices)

                beta = alpha = None
                if market_prices is not None:
                    combined = (
                        pd.concat([prices, market_prices], axis=1, join='inner')
                          .pct_change().dropna()
                    )
                    combined.columns = ["stock", "market"]
                    if not combined.empty:
                        beta  = calculate_beta(combined["stock"], combined["market"])
                        alpha = calculate_alpha(combined["stock"], combined["market"], beta)

                # fetch or create model instance
                indicator = db.session.get(StockIndicator, ticker)
                if not indicator:
                    indicator = StockIndicator(ticker=ticker)

                # assign native-Python values
                indicator.sector            = sector
                indicator.expected_return   = to_native(exp_ret)
                indicator.volatility        = to_native(vol)
                indicator.sharpe_ratio      = to_native(sr)
                indicator.max_drawdown      = to_native(mdd)
                indicator.value_at_risk     = to_native(var)
                indicator.beta              = to_native(beta)
                indicator.alpha             = to_native(alpha)
                indicator.last_updated      = datetime.now(timezone.utc)

                db.session.merge(indicator)
                print(f"Indicators calculated for {ticker} ({sector}).")

            except Exception as e:
                print(f"Failed to calculate indicators for {ticker}: {e}")

        db.session.commit()
        print("All indicators populated.")

if __name__ == "__main__":
    populate_stock_indicators()
