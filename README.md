# SimPill AI Hospital Ecosystem - Phase 1

This is the foundational phase of the SimPill AI Hospital Management System built using Flask, SQLAlchemy, and TailwindCSS.

## Features
- Modular Flask project structure (Blueprints)
- Authentication System (Login, Signup, Logout)
- Role-based Access Control (Patient, Doctor, Admin)
- Responsive Modern UI with TailwindCSS
- User Dashboards

## Getting Started

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the application:
```bash
python run.py
```

The app will create a local SQLite database `simpill.db` on the first run and will be available at `http://127.0.0.1:5000`.
