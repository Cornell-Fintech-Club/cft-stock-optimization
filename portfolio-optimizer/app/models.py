from app import db

class OHLCData(db.Model):
    __tablename__ = 'ohlc_data'
    
    id = db.Column(db.Integer, primary_key=True) 
    ticker = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    sector = db.Column(db.String(50), nullable=False)

class StockIndicator(db.Model):
    __tablename__ = 'stock_indicators'
    ticker = db.Column(db.String(10), primary_key=True)  # one row per stock
    sector = db.Column(db.String(50), nullable=False)
    expected_return = db.Column(db.Float, nullable=True)
    volatility = db.Column(db.Float, nullable=True)
    sharpe_ratio = db.Column(db.Float, nullable=True)
    max_drawdown = db.Column(db.Float, nullable=True)
    value_at_risk = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False)

