from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            identity = get_jwt_identity()
            if identity.get("role") not in roles:
                return jsonify({"error": "Unauthorized role"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper
