from flask import Blueprint, jsonify
from app.models import OHLCData
from app import db

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return jsonify({"message": "Flask Backend is Running!"})

@main.route("/ohlc/<ticker>", methods=["GET"])
def get_ohlc(ticker):
    data = OHLCData.query.filter_by(ticker=ticker).all()
    return jsonify([{
        'id': d.id,
        "ticker": d.ticker,
        "timestamp": d.timestamp,
        "open": d.open,
        "high": d.high,
        "low": d.low,
        "close": d.close,
        "volume": d.volume
    } for d in data])
