from flask import Blueprint, jsonify
from app.models import OHLCData
from app import db
from app.scraper import fetch_and_store_data 
import os 
from dotenv import load_dotenv
load_dotenv()

from flask import request
from datetime import datetime

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
            fetch_and_store_data(ticker)
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
