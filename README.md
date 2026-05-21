
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
# 🏥 SimPill  — Intelligent Hospital Management Ecosystem

<div align="center">

### AI-Powered Smart Healthcare & Hospital Automation Platform

*Transforming modern healthcare with Artificial Intelligence, automation, and digital patient care.*

</div>

---

# 📖 Overview

SimPill  is a next-generation AI-powered hospital management and patient care ecosystem developed to streamline healthcare operations for patients, doctors, caregivers, nurses, pharmacies, laboratories, and hospital administrators.

The platform integrates advanced hospital management functionalities with artificial intelligence to provide intelligent healthcare assistance, automated medicine adherence tracking, AI prescription recognition, telemedicine, emergency response systems, and healthcare analytics within a unified digital ecosystem.

SimPill  aims to bridge the gap between healthcare management and intelligent automation by delivering scalable, efficient, and user-centric healthcare solutions.

---

# ✨ Core Features

## 🔐 Authentication & Role Management
- Secure User Authentication
- Patient Registration & Login
- Doctor Registration & Login
- Admin Authentication
- Role-Based Access Control (RBAC)
- Password Encryption & Security
- Session Management
- CSRF Protection

---

## 👨‍⚕️ Patient Management System
- Digital Patient Profiles
- Medical History Tracking
- Prescription Management
- Medical Report Uploads
- Appointment Scheduling
- Medicine Adherence Monitoring
- Emergency Contact Management

---

## 🩺 Doctor Dashboard
- Patient Monitoring & Management
- Prescription Generation
- Appointment Approval System
- Medical Notes & Reports
- Consultation Management
- Patient History Access

---

## 💊 Smart Medicine Reminder System
- Automated Medicine Reminders
- Morning / Afternoon / Night Scheduling
- Before Food / After Food Notifications
- Missed Dose Tracking
- Caregiver Alert Notifications
- Daily Adherence Monitoring

---

# 🤖 AI-Powered Healthcare Features

## 🧠 AI Prescription OCR Scanner
- Handwritten Prescription Recognition
- Medicine Extraction
- Dosage Detection
- Timing & Duration Analysis

## 🤖 AI Health Assistant
- Symptom-Based Assistance
- Medicine Information
- Healthcare Guidance
- Patient Support Chatbot

## 📊 AI Report Analyzer
- Medical Report Analysis
- Abnormal Value Detection
- Health Insights Generation

## 💡 Disease Prediction System
- Symptom Analysis
- AI-Based Disease Suggestions
- Smart Healthcare Insights

## 💊 Medicine Verification System
- Medicine Image Verification
- Wrong Medicine Detection
- Smart Medicine Validation

---

# 📞 Telemedicine System
- Video Consultations
- Audio Calls
- Real-Time Messaging
- Remote Patient Support

---

# 🧪 Pharmacy & Laboratory Modules

## Pharmacy Management
- Medicine Inventory Management
- Low Stock Monitoring
- Expiry Tracking
- Medicine Distribution

## Laboratory Management
- Lab Test Booking
- Medical Report Uploads
- Report Generation
- AI-Assisted Report Analysis

---

# 🚨 Emergency Management System
- Emergency SOS Alerts
- Ambulance Request System
- Emergency Contact Notifications
- Rapid Emergency Access

---

# 📈 Analytics & Insights
- Patient Analytics Dashboard
- Appointment Statistics
- Medicine Adherence Analytics
- AI Health Insights
- Hospital Performance Monitoring

---

# 🛠 Technology Stack

## Frontend
- HTML5
- CSS3
- TailwindCSS
- JavaScript

## Backend
- Python Flask
- Flask-Login
- Flask-WTF
- SQLAlchemy

## Database
- SQLite *(PostgreSQL-ready architecture)*

## Artificial Intelligence & Integrations
- Tesseract OCR
- OpenCV
- spaCy
- Transformers
- Ollama
- Twilio API

---

# 📁 Project Architecture

```bash
simpill_ai/
│
├── app/
│   ├── auth/
│   ├── patient/
│   ├── doctor/
│   ├── admin/
│   ├── ai/
│   ├── pharmacy/
│   ├── laboratory/
│   ├── emergency/
│   ├── templates/
│   ├── static/
│   └── models/
│
├── uploads/
├── migrations/
├── requirements.txt
├── config.py
├── run.py
└── README.md
```

---

# ⚙️ Installation Guide

## 1️⃣ Clone the Repository

```bash
git clone <repository-url>
cd simpill_ai
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

#### Windows
```bash
venv\Scripts\activate
```

#### Linux / macOS
```bash
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Run the Application

>>>>>>> e67abc3db84153b08402916a49c86b8a7cca6ac8
```bash
python run.py
```

The app will create a local SQLite database `simpill.db` on the first run and will be available at `http://127.0.0.1:5000`.
=======
---

# 🚀 Future Enhancements

- Flutter Mobile Application
- PostgreSQL Migration
- Cloud Deployment
- Wearable Device Integration
- Predictive Healthcare Analytics
- AI Voice Assistant
- Multi-Hospital Architecture
- Smart ICU Monitoring
- Real-Time Health Monitoring

---

# 🎯 Vision

The vision of SimPill AI is to evolve into a fully integrated AI-powered digital healthcare ecosystem capable of enabling intelligent healthcare automation, remote patient monitoring, predictive analytics, and scalable hospital operations for modern healthcare infrastructures.

---

<div align="center">

### 👨‍💻 Developed By
# Sarwina Muralikrishnan (https://github.com/SarwinaMuralikrishnan)

</div>

