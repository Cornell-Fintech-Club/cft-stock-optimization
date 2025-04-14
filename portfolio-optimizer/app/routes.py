from flask import Blueprint, jsonify
from app.models import OHLCData
from app import db
from app.scraper import fetch_and_store_data 
import os 
from dotenv import load_dotenv
load_dotenv()
import numpy as np

from flask import request
from datetime import datetime

from analytics.data import fetch_daily_adjusted, fetch_multiple_series, align_price_series
from analytics.indicators import (
    calculate_expected_return,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_var,
)
from analytics.portfolio import compute_portfolio_metrics


main = Blueprint("main", __name__)

@main.route("/update_data", methods=["GET"])
def update_stock_data():
    # tickers = ["AAPL", "GOOG", "MSFT"]  # example tickers
    # for ticker in tickers:
    #     fetch_and_store_data(ticker)  # Call the function to fetch and store data
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error":"Incorrectly formatted Ticker symobl"}), 400
    fetch_and_store_data(ticker)
    return jsonify({"message": "Stock data updated successfully!"}), 200

@main.route("/")
def home():
    return jsonify({"message": "Flask Backend is Running!"})

@main.route("/ohlc/<ticker>", methods=["GET"])
def get_ohlc(ticker):
    start_date = request.args.get("start_date", None)
    end_date = request.args.get("end_date", None)

    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD."}), 400

    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD."}), 400

    # data = OHLCData.query.filter_by(ticker=ticker).all()
    # query = OHLCData.query.filter_by(ticker=ticker)

    query = OHLCData.query.filter(OHLCData.ticker == ticker)

    if start_date:
        query = query.filter(OHLCData.timestamp >= start_date)
    if end_date:
        query = query.filter(OHLCData.timestamp <= end_date)

    data = query.all()
    
    if not data:
        existing_data = OHLCData.query.filter_by(ticker=ticker).first()
        # print(f"No data found for {ticker} in range {start_date} to {end_date}. Fetching new data...")
        # print(existing_data)
        if not existing_data:
            fetch_and_store_data(ticker,start_date=start_date,end_date=end_date)
            db.session.commit()

            query = OHLCData.query.filter(OHLCData.ticker == ticker)
            if start_date:
                query = query.filter(OHLCData.timestamp >= start_date)
            if end_date:
                query = query.filter(OHLCData.timestamp <= end_date)
            data = query.all()
            if not data:
                return jsonify({"error": "Data not found for this ticker and date range."}), 404
    
    return jsonify([{
        'id': d.id,
        "ticker": d.ticker,
        "timestamp": d.timestamp,
        "open": d.open,
        "high": d.high,
        "low": d.low,
        "close": d.close,
        "volume": d.volume
    } for d in data]),200



api = Blueprint("api", __name__)

@api.route("/api/metrics/<symbol>", methods=["GET"])
def stock_metrics(symbol):
    try:
        series = fetch_daily_adjusted(symbol)
        metrics = {
            "expected_return": calculate_expected_return(series),
            "volatility": calculate_volatility(series),
            "sharpe_ratio": calculate_sharpe_ratio(series),
            "max_drawdown": calculate_max_drawdown(series),
            "value_at_risk": calculate_var(series),
        }
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api.route("/api/portfolio/metrics", methods=["POST"])
def portfolio_metrics():
    try:
        data = request.json
        symbols = data["symbols"]              # e.g., ["AAPL", "MSFT", "JNJ"]
        weights = np.array(data["weights"])    # e.g., [0.4, 0.4, 0.2]

        price_dict = fetch_multiple_series(symbols)
        price_df = align_price_series(price_dict)

        results = compute_portfolio_metrics(price_df, weights)
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 400
