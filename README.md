# MedBeta - Backend

This repository contains the backend API for MedBeta, a medical appointment and records management system.

## Overview

The backend is built with Flask and SQLAlchemy and provides REST endpoints to manage users, doctors, hospitals, appointments, medical records, prescriptions, pharmacies, technicians, and reviews. It uses JWT for authentication and supports environment-based configuration.

## Tech stack

- Python 3.8+
- Flask
- SQLAlchemy (Flask-SQLAlchemy)
- Alembic for migrations
- Pipenv for dependency management (Pipfile provided)

## Repository layout (top-level)

- `app/` - application package (models, routes, utils, config)
- `migrations/` - Alembic migrations
- `main.py` - application entrypoint
- `Pipfile` - Pipenv dependency file

## Quick start

1. Clone the repository

```bash
git clone <repo-url>
cd MedBeta-Backend
```

2. Install dependencies (using Pipenv) and activate a shell

```bash
pipenv install --dev
pipenv shell
```

Alternatively, create a venv and install with pip:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # if you generate one from Pipfile
```

3. Create an `.env` file in the project root (see Environment Variables below)

4. Apply database migrations

```bash
pipenv run flask db upgrade
# or if using flask-migrate directly
# flask db upgrade
```

5. Run the application

```bash
pipenv run python main.py
# or
python main.py
```

## Environment variables

The backend reads configuration from environment variables (see `app/config.py`). Example variables you should set in `.env` or your environment:

- `DATABASE_URL` - SQLAlchemy database URL (e.g. `postgresql://user:pass@localhost:5432/medbeta`)
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - Secret used for JWT tokens
- `ENCRYPTION_KEY` - Key used for any encrypted fields

Example `.env` (DO NOT commit secrets to source control):

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/medbeta
SECRET_KEY=replace-with-a-random-secret
JWT_SECRET_KEY=replace-with-jwt-secret
ENCRYPTION_KEY=replace-with-encryption-key
```

## Database migrations

Alembic is configured under `migrations/`. Use Flask-Migrate or Alembic CLI to generate and apply migration scripts.

## Running tests

There is a `test_email.py` in the project root as an example test. Run tests using pytest if you add tests to the project.

```bash
pipenv run pytest -q
```

## API routes overview

Routes are organized in `app/routes/`. Notable route modules include:

- `auth_routes.py` - authentication (login/register)
- `appoint_routes.py` - appointment endpoints
- `patient_routes.py` - patient related endpoints
- `doctor_route.py` - doctor actions
- `prescription.py` - prescriptions
- `hospital.py` - hospital endpoints
- `lab.py` - lab/technician related endpoints
- `review_routes.py` - reviews
- `Access_routes.py` and `admin_routes.py` - access control and admin

For a complete list of endpoints, open the route files in `app/routes/` or run the app and use an API client (Postman/Insomnia) to explore.

## Configuration

See `app/config.py` for SQLAlchemy and other configuration. The config class loads values from environment variables via `python-dotenv`.

## Contributors

- Cynthia Mugo
- Irene Murage
- Wayne Muongi
- Horace Kauna
- Ian Mabruk

If you'd like to add yourself as a contributor, please open a pull request updating this file.

## License

This project is designed to enhance hands on practical expertise and understanding of the beauty of backend development under the instruction of Moringa School.

## Contact

For questions or help with the backend, open an issue or contact one of the contributors listed above.

---

Note: Adjust the command examples to your environment (virtualenv, pipenv, or system python). Keep secrets out of source control and use a secure vault for production credentials.