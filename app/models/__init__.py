from datetime import datetime, time
import secrets
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient') # patient, doctor, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient_profile = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    doctor_profile = db.relationship('Doctor', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)

    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    medicines = db.relationship('Medicine', backref='patient', lazy=True)
    reports = db.relationship('Report', backref='patient', lazy=True)
    caregivers = db.relationship('Caregiver', backref='patient', lazy=True)
    lab_bookings = db.relationship('LabTestBooking', backref='patient', lazy=True)
    invoices = db.relationship('Invoice', backref='patient', lazy=True)
    emergency_requests = db.relationship('EmergencyRequest', backref='patient', lazy=True)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    experience = db.Column(db.Integer, nullable=True) # years of experience
    available_from = db.Column(db.Time, default=time(9, 0), nullable=False)
    available_to = db.Column(db.Time, default=time(17, 0), nullable=False)
    available_days = db.Column(db.String(255), default='Monday,Tuesday,Wednesday,Thursday,Friday', nullable=False)
    
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Completed, Cancelled
    notes = db.Column(db.Text, nullable=True)
    is_telemedicine = db.Column(db.Boolean, default=False, nullable=False)
    room_id = db.Column(db.String(100), nullable=True)

class Medicine(db.Model):
    __tablename__ = 'medicines'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    timing = db.Column(db.String(50), nullable=False) # Before food, After food
    duration = db.Column(db.String(50), nullable=False) # e.g. 7 days
    reminders = db.relationship('Reminder', backref='medicine', lazy=True, cascade='all, delete-orphan')

class Reminder(db.Model):
    __tablename__ = 'reminders'
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    reminder_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Taken, Missed
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), default='Report', nullable=False) # Prescription, Report, Medical Scan
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Caregiver(db.Model):
    __tablename__ = 'caregivers'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    caregiver_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    relation = db.Column(db.String(50), nullable=False)
    token = db.Column(db.String(64), unique=True, default=lambda: secrets.token_hex(16), nullable=False)

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    price = db.Column(db.Float, default=0.0, nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=True)
    low_stock_threshold = db.Column(db.Integer, default=10, nullable=False)

class LabTestBooking(db.Model):
    __tablename__ = 'lab_test_bookings'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    test_name = db.Column(db.String(100), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Completed
    result_pdf = db.Column(db.String(255), nullable=True)
    result_explanation = db.Column(db.Text, nullable=True)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    items_json = db.Column(db.Text, nullable=False) # JSON serialized description of items: [{"name": "...", "price": 0.0, "qty": 1}]
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False) # GST (18%)
    total = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='Pending') # Pending, Paid
    payment_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmergencyRequest(db.Model):
    __tablename__ = 'emergency_requests'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Active') # Active, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
