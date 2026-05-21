from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.admin import bp
from app import db
from app.models import User, Doctor, Patient, Appointment, Invoice, LabTestBooking, InventoryItem, EmergencyRequest

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
        
    total_users = User.query.count()
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    total_labs = LabTestBooking.query.count()
    total_inventory = InventoryItem.query.count()
    
    # Calculate revenue
    paid_invoices = Invoice.query.filter_by(payment_status='Paid').all()
    revenue = sum(inv.total for inv in paid_invoices)
    
    # Count emergencies
    active_emergencies = EmergencyRequest.query.filter_by(status='Active').count()
    
    # Simple Mock occupancy and disease trends for dashboard display
    occupancy = 76 # 76% occupancy
    disease_trends = [
        {"disease": "Hypertension", "cases": 45, "percentage": 30},
        {"disease": "Diabetes Mellitus", "cases": 32, "percentage": 21},
        {"disease": "Bacterial Bronchitis", "cases": 28, "percentage": 18},
        {"disease": "Gastroenteritis", "cases": 25, "percentage": 16},
        {"disease": "Vitamin Deficiencies", "cases": 20, "percentage": 13}
    ]
    
    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html', 
        title='Admin Portal',
        total_users=total_users,
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_labs=total_labs,
        total_inventory=total_inventory,
        revenue=round(revenue, 2),
        active_emergencies=active_emergencies,
        occupancy=occupancy,
        disease_trends=disease_trends,
        recent_invoices=recent_invoices
    )
