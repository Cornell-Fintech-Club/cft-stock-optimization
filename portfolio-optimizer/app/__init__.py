from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_cors import CORS



db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)    

    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    from app.routes import api
    app.register_blueprint(api)

    from app.routes import api2
    app.register_blueprint(api2)

    
    return app
