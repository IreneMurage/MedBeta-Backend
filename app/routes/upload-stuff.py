#  Bulk upload staff (Superadmin)

@superadmin_bp.route("/upload-staff", methods=["POST"])
@role_required("superadmin")
def upload_staff():
    """
    Allows Superadmin to upload a CSV or JSON list of users (staff) for any hospital.
    Each invite creates a PendingUser record and sends an email with a verification link.
    """
    file = request.files.get("file")
    data = request.get_json() if request.is_json else None
    staff_data = []

    if file and file.filename.endswith(".csv"):
        import csv, io
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        staff_data = [row for row in reader]
    elif data:
        staff_data = data.get("staff", [])
    else:
        return jsonify({"error": "Please upload a CSV file or JSON with 'staff' key"}), 400

    if not staff_data:
        return jsonify({"error": "No staff data found"}), 400

    invites_sent = []
    for person in staff_data:
        email = person.get("email")
        name = person.get("name")
        role = person.get("role")
        hospital_id = person.get("hospital_id")

        if not all([email, name, role]):
            continue

        # Skip if user or pending already exists
        if User.query.filter_by(email=email).first() or PendingUser.query.filter_by(email=email).first():
            continue

        # Generate unique token
        token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)

        pending = PendingUser(
            email=email,
            name=name,
            role=role,
            hospital_id=hospital_id,
            invite_token=token,
            expires_at=expires_at,
            is_accepted=False,
        )
        db.session.add(pending)

        # Email invite link
        verify_link = f"{request.host_url}auth/setup-password/{token}"
        try:
            send_invite_email(email, token)
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")
        invites_sent.append(email)

    db.session.commit()

    return jsonify({
        "message": f"Invites sent successfully to {len(invites_sent)} users",
        "emails": invites_sent
    }), 201
