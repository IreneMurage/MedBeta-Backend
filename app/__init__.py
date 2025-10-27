from flask import Flask
from .config import Config
from .db import db,migrate
from .models import *
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager

bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)

    # initialize db
    db.init_app(app)
    migrate.init_app(app,db)
    bcrypt.init_app(app)
    CORS(app, supports_credentials=True)
    jwt.init_app(app)



    
    return app