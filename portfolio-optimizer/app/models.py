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
