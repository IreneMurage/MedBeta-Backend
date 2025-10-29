from flask import Flask
from .config import Config
from .db import db, migrate
from .models import *
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from app.routes import auth_bp, appointment_bp, medical_bp, superadmin_bp, patient_bp, doctor_bp, hospital_bp, lab_bp, pharmacy_bp, prescription_bp, review_bp
from flask_cors import CORS




from app.routes.patient_routes import patient_bp


bcrypt = Bcrypt()
jwt = JWTManager()

# # Fix for 422 "Subject must be a string"
# @jwt.user_identity_loader
# def user_identity_lookup(identity):
#     return str(identity["id"]) 

# @jwt.additional_claims_loader
# def add_claims_to_access_token(identity):
#     return {"role": identity["role"]}  # store role in token claims

def create_superadmin_if_needed():
    from app.models import User

    email = os.getenv("SUPERADMIN_EMAIL")
    password = os.getenv("SUPERADMIN_PASSWORD")
    name = os.getenv("SUPERADMIN_NAME", "Super Admin")

    if not email or not password:
        print(" SUPERADMIN credentials not set in .env")
        return

    existing_user = User.query.filter_by(email=email).first()
    if not existing_user:
        superadmin = User(
            name=name,
            email=email,
            role="superadmin",
            is_active=True,
            status="active"
        )
        superadmin.set_password(password)
        db.session.add(superadmin)
        db.session.commit()
        print(f"SuperAdmin created automatically: {email}")
    else:
        print(f"SuperAdmin already exists: {email}")



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    # Initialize db and migrations
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)


    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(appointment_bp, url_prefix='/appointments')
    app.register_blueprint(medical_bp, url_prefix='/medical-records')
    app.register_blueprint(superadmin_bp, url_prefix='/admin')

    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(lab_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(review_bp, url_prefix='/reviews')
    

    app.register_blueprint(patient_bp, url_prefix='/patients')
    




    # Ensure SuperAdmin exists
    with app.app_context():
        db.create_all()
        create_superadmin_if_needed()


    #  Register Blueprints
    # app.register_blueprint(patient_bp)

    @app.route("/")
    def home():
        return {"message": "MedBeta API is running"}

    

    return app
  
