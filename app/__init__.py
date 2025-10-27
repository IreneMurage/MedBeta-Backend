from flask import Flask
from .config import Config
from .db import db,migrate
from .models import *
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)

    # initialize db
    db.init_app(app)
    migrate.init_app(app,db)

    # initialize bcrypt
    bcrypt.init_app(app)

    return app




