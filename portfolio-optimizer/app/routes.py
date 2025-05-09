from flask import Blueprint, jsonify, request
from app.models import OHLCData, StockIndicator
from app import db
from app.scraper import fetch_and_store_data 
import numpy as np
from datetime import datetime, timedelta, timezone
from optimizers.optimize_rebalance import rebalance_portfolio
from optimizers.optimize_add import optimize_with_greedy_addition
import yfinance as yf
import copy

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

    # Query for existing data in the DB
    query = OHLCData.query.filter(OHLCData.ticker == ticker)
    if start_date:
        query = query.filter(OHLCData.timestamp >= start_date)
    if end_date:
        query = query.filter(OHLCData.timestamp <= end_date)

    data = query.all()

    # If nothing exists for the range, try fetching from yfinance
    if not data:
        print(f"No data found for {ticker} in range {start_date} to {end_date}. Fetching from yfinance...")
        fetch_and_store_data(ticker, start_date=start_date, end_date=end_date)
        db.session.commit()

        # Retry query after insert
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
        "volume": d.volume,
        "sector": d.sector
    } for d in data]), 200


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

@api.route('/api/price_history/<string:ticker>', methods=['GET'])
def get_price_history(ticker):
    try:
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        records = (
            db.session.query(OHLCData)
            .filter(OHLCData.ticker == ticker.upper())
            .filter(OHLCData.timestamp >= one_year_ago)
            .order_by(OHLCData.timestamp.asc())
            .all()
        )

        if not records:
            return jsonify({"message": f"No price data found for {ticker}"}), 404

        result = [
            {
                "open": record.open,
            }
            for record in records
        ]
        return jsonify({"ticker": ticker.upper(), "price_history": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    tickers = StockIndicator.query.with_entities(StockIndicator.ticker).all()
    result = []

    for t in tickers:
        try:
            info = yf.Ticker(t.ticker).info
            name = info.get("shortName", "N/A")
        except Exception:
            name = "N/A"
        result.append({
            "ticker": t.ticker,
            "name": name
        })

    return jsonify({"stocks": result})  



api2 = Blueprint("optimizer", __name__)

@api2.route("/api/optimize_portfolio", methods=["POST"])
def optimize_portfolio():
    try:
        data = request.json or {}
        survey  = data.get("survey")
        symbols = data.get("symbols", [])
        weights = data.get("weights", [])
        print("Survey:", survey)
        print("Symbols:", symbols)
        print("Weights:", weights)

        if not survey or not symbols or not weights:
            return jsonify({"error": "Missing required fields: survey, symbols, weights"}), 400
        print("1")
        # Step 1: Calculate original portfolio metrics
        print("2")
        price_dict       = fetch_multiple_series(symbols)
        print("3")
        price_df         = align_price_series(price_dict)
        print("4")
        weights_array    = np.array(weights, dtype=float)
        print("5")
        original_metrics = compute_portfolio_metrics(price_df, weights_array)

        # Step 2: Choose optimizer
        print("6")
        if survey.get("addAssets", False):
            print("20")
            # Greedy-addition optimizer
            result = optimize_with_greedy_addition(survey, symbols.copy(), weights.copy())
            print("21")
        else:
            # Pure rebalance optimizer
            print("7")
            result = rebalance_portfolio(survey, symbols.copy(), weights.copy())
        
        # Always attach the “before” snapshot
        print("8")
        result.setdefault("original_metrics", original_metrics)
        result.setdefault("original_symbols",  symbols)
        result.setdefault("original_weights",  weights)

        # If rebalance produced only weights, attach symbols list
        if result.get("optimized_weights") and "optimized_symbols" not in result:
            result["optimized_symbols"] = symbols

        print(result)
        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@api.route("/api/indicator/<symbol>", methods=["GET"])
def get_stock_indicators(symbol):
    try:
        indicator = StockIndicator.query.get(symbol.upper())
        if not indicator:
            return jsonify({"error": f"No indicator data found for {symbol}"}), 404

        return jsonify({
            "ticker": indicator.ticker,
            "expected_return": indicator.expected_return,
            "volatility": indicator.volatility,
            "sharpe_ratio": indicator.sharpe_ratio,
            "beta": indicator.beta,
            "alpha": indicator.alpha,
            "max_drawdown": indicator.max_drawdown,
            "value_at_risk": indicator.value_at_risk,
            "diversification_score": indicator.diversification_score
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500