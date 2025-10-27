from app.models import AccessLog
from app.db import db
from app.utils.time import utc_now

def log_access(doctor_id, patient_id, purpose="viewed record"):
    log = AccessLog(
        doctor_id=doctor_id,
        patient_id=patient_id,
        purpose=purpose,
        accessed_at=utc_now()
    )
    db.session.add(log)
    db.session.commit()
