from flask import Flask
from .config import Config
from .db import db, migrate
from .models import *
from flask_bcrypt import Bcrypt

from app.routes.patient import patient_bp

bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize db and migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize bcrypt
    bcrypt.init_app(app)

    # ✅ Register Blueprints
    app.register_blueprint(patient_bp)

    @app.route("/")
    def home():
        return {"message": "MedBeta API is running"}
    

    return app
