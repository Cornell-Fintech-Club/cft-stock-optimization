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

app = create_app()

def fetch_close_prices_and_sector(ticker):
    """Fetch close prices and sector from ohlc_data for a given ticker."""
    records = (
        OHLCData.query.filter_by(ticker=ticker)
        .order_by(OHLCData.timestamp.asc())
        .all()
    )
    if not records:
        return None, None

    close_prices = pd.Series({r.timestamp: r.close for r in records})
    sector = records[0].sector if records else None

    return close_prices, sector

def fetch_market_prices():
    """Fetch benchmark (e.g., SPY) close prices for beta/alpha."""
    spy_records = (
        OHLCData.query.filter_by(ticker="SPY")
        .order_by(OHLCData.timestamp.asc())
        .all()
    )
    if not spy_records:
        return None
    return pd.Series({r.timestamp: r.close for r in spy_records})

def populate_stock_indicators():
    with app.app_context():
        print("Clearing existing stock_indicators table...")
        db.session.execute(text('TRUNCATE TABLE stock_indicators;'))
        db.session.commit()

        tickers = db.session.query(OHLCData.ticker).distinct().all()
        tickers = [t[0] for t in tickers]
        print(f"Found {len(tickers)} tickers. Calculating indicators...")

        market_prices = fetch_market_prices()

        for ticker in tickers:
            prices, sector = fetch_close_prices_and_sector(ticker)
            if prices is None or len(prices) < 2 or sector is None:
                print(f"Skipping {ticker} due to insufficient data or missing sector.")
                continue

            try:
                expected_return = calculate_expected_return(prices)
                volatility = calculate_volatility(prices)
                sharpe_ratio = calculate_sharpe_ratio(prices)
                max_drawdown = calculate_max_drawdown(prices)
                value_at_risk = calculate_var(prices)

                beta = alpha = None
                if market_prices is not None:
                    combined = pd.concat([prices.pct_change(), market_prices.pct_change()], axis=1).dropna()
                    combined.columns = ["stock", "market"]
                    beta = calculate_beta(combined["stock"], combined["market"])
                    alpha = calculate_alpha(combined["stock"], combined["market"], beta)

                indicator = db.session.get(StockIndicator, ticker)
                if not indicator:
                    indicator = StockIndicator(ticker=ticker)

                indicator.sector = sector
                indicator.expected_return = expected_return
                indicator.volatility = volatility
                indicator.sharpe_ratio = sharpe_ratio
                indicator.max_drawdown = max_drawdown
                indicator.value_at_risk = value_at_risk
                indicator.beta = beta
                indicator.alpha = alpha
                indicator.last_updated = datetime.now(timezone.utc)

                db.session.merge(indicator)
                print(f"Indicators calculated for {ticker} ({sector}).")

            except Exception as e:
                print(f"Failed to calculate indicators for {ticker}: {e}")

        db.session.commit()
        print("All indicators populated.")

if __name__ == "__main__":
    populate_stock_indicators()
