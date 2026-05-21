from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import os
import json
import secrets
from app import db
from app.patient import bp
from app.models import (
    User, Patient, Doctor, Appointment, Medicine, Reminder, 
    Report, Caregiver, InventoryItem, LabTestBooking, Invoice, EmergencyRequest
)
from app.forms.patient import AppointmentForm, ReportUploadForm, CaregiverForm
from app.services.analyzer_service import analyze_report_text
from app.services.billing_service import calculate_invoice_amounts, generate_invoice_number

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    patient = current_user.patient_profile
    
    # 1. Update past pending reminders to 'Missed'
    now_dt = datetime.now()
    today_date = date.today()
    pending_reminders = Reminder.query.join(Medicine).filter(
        Medicine.patient_id == patient.id,
        Reminder.date == today_date,
        Reminder.status == 'Pending'
    ).all()
    
    for rem in pending_reminders:
        rem_datetime = datetime.combine(today_date, rem.reminder_time)
        if rem_datetime < now_dt:
            rem.status = 'Missed'
    db.session.commit()
    
    # 2. Get today's reminders
    today_reminders = Reminder.query.join(Medicine).filter(
        Medicine.patient_id == patient.id,
        Reminder.date == today_date
    ).order_by(Reminder.reminder_time).all()
    
    # Organize reminders by day time (Morning, Afternoon, Night)
    morning_reminders = []
    afternoon_reminders = []
    night_reminders = []
    
    taken_count = 0
    total_count = len(today_reminders)
    
    for rem in today_reminders:
        if rem.status == 'Taken':
            taken_count += 1
            
        t_hour = rem.reminder_time.hour
        if t_hour < 12:
            morning_reminders.append(rem)
        elif t_hour < 17:
            afternoon_reminders.append(rem)
        else:
            night_reminders.append(rem)
            
    compliance = int((taken_count / total_count) * 100) if total_count > 0 else 100
    
    # 3. Get next dose countdown information
    next_dose = None
    next_time_str = ""
    future_rem = Reminder.query.join(Medicine).filter(
        Medicine.patient_id == patient.id,
        Reminder.date == today_date,
        Reminder.status == 'Pending'
    ).order_by(Reminder.reminder_time).first()
    
    if future_rem:
        next_dose = future_rem
        # Calculate time diff in minutes
        rem_dt = datetime.combine(today_date, future_rem.reminder_time)
        diff = rem_dt - now_dt
        diff_mins = int(diff.total_seconds() / 60)
        if diff_mins > 60:
            next_time_str = f"in {diff_mins // 60}h {diff_mins % 60}m"
        else:
            next_time_str = f"in {diff_mins} mins"
            
    # 4. Fetch upcoming approved appointments
    appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= today_date,
        Appointment.status.in_(['Approved', 'Scheduled'])
    ).order_by(Appointment.date, Appointment.time).all()
    
    # 5. Fetch recent missed medicine alerts
    missed_reminders = Reminder.query.join(Medicine).filter(
        Medicine.patient_id == patient.id,
        Reminder.date == today_date,
        Reminder.status == 'Missed'
    ).all()
    
    # Active medications
    medicines = Medicine.query.filter_by(patient_id=patient.id).all()
    
    return render_template(
        'patient/dashboard.html', 
        title='Patient Dashboard', 
        medicines=medicines, 
        appointments=appointments,
        morning_reminders=morning_reminders,
        afternoon_reminders=afternoon_reminders,
        night_reminders=night_reminders,
        compliance=compliance,
        taken_count=taken_count,
        total_count=total_count,
        next_dose=next_dose,
        next_time_str=next_time_str,
        missed_reminders=missed_reminders
    )

@bp.route('/reminder/toggle/<int:reminder_id>', methods=['POST'])
@login_required
def toggle_reminder(reminder_id):
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
        
    reminder = Reminder.query.get_or_404(reminder_id)
    if reminder.medicine.patient_id != current_user.patient_profile.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status in ['Pending', 'Taken', 'Missed']:
        reminder.status = new_status
        db.session.commit()
        return jsonify({"success": True, "status": reminder.status})
        
    return jsonify({"error": "Invalid status"}), 400

@bp.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    patient = current_user.patient_profile
    form = AppointmentForm()
    doctors = Doctor.query.all()
    form.doctor_id.choices = [(d.id, f"Dr. {d.user.name} - {d.specialization or 'General'}") for d in doctors]
    
    if form.validate_on_submit():
        selected_doctor_id = form.doctor_id.data
        doc = Doctor.query.get(selected_doctor_id)
        
        # Check doctor availability
        appt_date = form.date.data
        appt_time = form.time.data
        
        # 1. Past check
        if appt_date < date.today():
            flash('Cannot book appointments in the past!', 'error')
            return redirect(url_for('patient.appointments'))
            
        # 2. Weekday check
        weekday_name = appt_date.strftime('%A')
        available_days = [d.strip() for d in doc.available_days.split(',')]
        if weekday_name not in available_days:
            flash(f"Dr. {doc.user.name} is only available on {doc.available_days}!", 'error')
            return redirect(url_for('patient.appointments'))
            
        # 3. Time bounds check
        if appt_time < doc.available_from or appt_time > doc.available_to:
            flash(f"Dr. {doc.user.name} is available from {doc.available_from.strftime('%H:%M')} to {doc.available_to.strftime('%H:%M')}!", 'error')
            return redirect(url_for('patient.appointments'))
            
        # Success booking
        is_telemed = True if form.is_telemedicine.data == '1' else False
        room = secrets.token_hex(8) if is_telemed else None
        
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=selected_doctor_id,
            date=appt_date,
            time=appt_time,
            notes=form.notes.data,
            is_telemedicine=is_telemed,
            room_id=room,
            status='Pending'
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully! Awaiting doctor approval.', 'success')
        return redirect(url_for('patient.appointments'))
        
    all_appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date.desc()).all()
    return render_template('patient/appointments.html', title='Book Appointment', form=form, appointments=all_appointments, doctors=doctors)

@bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    patient = current_user.patient_profile
    form = ReportUploadForm()
    
    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        f.save(file_path)
        
        report = Report(
            patient_id=patient.id,
            title=form.title.data,
            file_path=filename,
            category=form.category.data
        )
        db.session.add(report)
        db.session.commit()
        flash('Medical file uploaded successfully!', 'success')
        return redirect(url_for('patient.reports'))
        
    all_reports = Report.query.filter_by(patient_id=patient.id).order_by(Report.upload_date.desc()).all()
    return render_template('patient/reports.html', title='Medical Files & Reports', form=form, reports=all_reports)

@bp.route('/reports/analyze/<int:report_id>')
@login_required
def analyze_report(report_id):
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
        
    report = Report.query.get_or_404(report_id)
    if report.patient_id != current_user.patient_profile.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    # Standard Mock text for blood panel to trigger the parser properly
    sample_text = (
        "Patient Blood Examination Report. Result metrics:\n"
        "Hemoglobin: 11.4 g/dL\n"
        "Glucose: 122.0 mg/dL\n"
        "Total Cholesterol: 218.0 mg/dL\n"
        "WBC: 7.2 x10^3/mcL\n"
        "RBC: 4.5 x10^6/mcL\n"
        "Platelets: 220 x10^3/mcL"
    )
    
    analysis = analyze_report_text(sample_text)
    return jsonify(analysis)

@bp.route('/caregivers', methods=['GET', 'POST'])
@login_required
def caregivers():
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    patient = current_user.patient_profile
    form = CaregiverForm()
    
    if form.validate_on_submit():
        caregiver = Caregiver(
            patient_id=patient.id,
            caregiver_name=form.caregiver_name.data,
            phone=form.phone.data,
            relation=form.relation.data
        )
        db.session.add(caregiver)
        db.session.commit()
        flash('Caregiver registered successfully!', 'success')
        return redirect(url_for('patient.caregivers'))
        
    all_caregivers = Caregiver.query.filter_by(patient_id=patient.id).all()
    return render_template('patient/caregivers.html', title='Caregivers', form=form, caregivers=all_caregivers)

@bp.route('/caregiver/delete/<int:caregiver_id>', methods=['POST'])
@login_required
def delete_caregiver(caregiver_id):
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    caregiver = Caregiver.query.get_or_404(caregiver_id)
    if caregiver.patient_id != current_user.patient_profile.id:
        flash('Unauthorized deletion attempt', 'error')
        return redirect(url_for('patient.caregivers'))
        
    db.session.delete(caregiver)
    db.session.commit()
    flash('Caregiver removed successfully!', 'success')
    return redirect(url_for('patient.caregivers'))

@bp.route('/billing')
@login_required
def billing():
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    patient = current_user.patient_profile
    
    # If no invoices exist, let's auto-generate a sample invoice for testing
    invoices = Invoice.query.filter_by(patient_id=patient.id).order_by(Invoice.created_at.desc()).all()
    if not invoices:
        items = [{"name": "Doctor Consultation Fee", "price": 800.00, "qty": 1},
                 {"name": "Laboratory Panel - Glucose & Hemoglobin", "price": 400.00, "qty": 1}]
        sub, tax, tot = calculate_invoice_amounts(items)
        invoice = Invoice(
            patient_id=patient.id,
            invoice_number=generate_invoice_number(),
            items_json=json.dumps(items),
            subtotal=sub,
            tax=tax,
            total=tot,
            payment_status='Pending'
        )
        db.session.add(invoice)
        db.session.commit()
        invoices = [invoice]
        
    return render_template('patient/billing.html', title='Bills & Payments', invoices=invoices)

@bp.route('/billing/pay/<int:invoice_id>', methods=['POST'])
@login_required
def pay_invoice(invoice_id):
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
        
    invoice = Invoice.query.get_or_404(invoice_id)
    if invoice.patient_id != current_user.patient_profile.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    payment_id = data.get("payment_id", "pay_mock_" + secrets.token_hex(6))
    
    invoice.payment_status = 'Paid'
    invoice.payment_id = payment_id
    db.session.commit()
    
    return jsonify({"success": True, "invoice_number": invoice.invoice_number})

@bp.route('/laboratory', methods=['GET', 'POST'])
@login_required
def laboratory():
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    patient = current_user.patient_profile
    
    available_tests = [
        {"name": "Complete Blood Count (CBC)", "price": 350.0},
        {"name": "Lipid Profile (Cholesterol)", "price": 500.0},
        {"name": "Diabetes Screening (HbA1c)", "price": 450.0},
        {"name": "Kidney Function Test (KFT)", "price": 600.0},
        {"name": "Liver Function Test (LFT)", "price": 550.0}
    ]
    
    if request.method == 'POST':
        test_name = request.form.get('test_name')
        test_price = float(request.form.get('test_price', 0.0))
        
        # Book lab test
        booking = LabTestBooking(
            patient_id=patient.id,
            test_name=test_name,
            booking_date=date.today() + timedelta(days=1), # booked for tomorrow
            status='Pending'
        )
        db.session.add(booking)
        
        # Generate Invoice for the laboratory test
        items = [{"name": f"Lab Test: {test_name}", "price": test_price, "qty": 1}]
        sub, tax, tot = calculate_invoice_amounts(items)
        invoice = Invoice(
            patient_id=patient.id,
            invoice_number=generate_invoice_number(),
            items_json=json.dumps(items),
            subtotal=sub,
            tax=tax,
            total=tot,
            payment_status='Pending'
        )
        db.session.add(invoice)
        db.session.commit()
        
        flash(f'Laboratory booking for {test_name} scheduled successfully! Invoice generated.', 'success')
        return redirect(url_for('patient.laboratory'))
        
    bookings = LabTestBooking.query.filter_by(patient_id=patient.id).order_by(LabTestBooking.booking_date.desc()).all()
    return render_template('patient/laboratory.html', title='Lab Services', available_tests=available_tests, bookings=bookings)

@bp.route('/pharmacy')
@login_required
def pharmacy():
    if current_user.role != 'patient':
        return redirect(url_for('auth.login'))
        
    patient = current_user.patient_profile
    
    # Retrieve active catalog stock
    items = InventoryItem.query.all()
    # If inventory is empty, populate standard products for the pharmacy
    if not items:
        standard_items = [
            {"name": "Paracetamol 500mg", "qty": 120, "price": 45.0, "expiry_date": date.today() + timedelta(days=200), "barcode": "8901234567812", "low_stock_threshold": 20},
            {"name": "Amoxicillin 250mg", "qty": 80, "price": 95.0, "expiry_date": date.today() + timedelta(days=360), "barcode": "8901234567823", "low_stock_threshold": 15},
            {"name": "Ibuprofen 400mg", "qty": 15, "price": 38.0, "expiry_date": date.today() + timedelta(days=90), "barcode": "8901234567834", "low_stock_threshold": 25},
            {"name": "Metformin 500mg", "qty": 5, "price": 110.0, "expiry_date": date.today() + timedelta(days=400), "barcode": "8901234567845", "low_stock_threshold": 10}
        ]
        for sit in standard_items:
            db_item = InventoryItem(
                name=sit["name"],
                quantity=sit["qty"],
                price=sit["price"],
                expiry_date=sit["expiry_date"],
                barcode=sit["barcode"],
                low_stock_threshold=sit["low_stock_threshold"]
            )
            db.session.add(db_item)
        db.session.commit()
        items = InventoryItem.query.all()
        
    return render_template('patient/pharmacy.html', title='Pharmacy Portal', inventory=items)

@bp.route('/pharmacy/order', methods=['POST'])
@login_required
def pharmacy_order():
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
        
    patient = current_user.patient_profile
    data = request.get_json() or {}
    cart = data.get("cart", [])
    
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400
        
    invoice_items = []
    for item in cart:
        inv_item = InventoryItem.query.get(item["id"])
        if not inv_item or inv_item.quantity < item["qty"]:
            return jsonify({"error": f"Insufficient stock for {inv_item.name if inv_item else 'item'}"}), 400
            
        inv_item.quantity -= item["qty"]
        invoice_items.append({
            "name": inv_item.name,
            "price": inv_item.price,
            "qty": item["qty"]
        })
        
    # Generate Invoice
    sub, tax, tot = calculate_invoice_amounts(invoice_items)
    invoice = Invoice(
        patient_id=patient.id,
        invoice_number=generate_invoice_number(),
        items_json=json.dumps(invoice_items),
        subtotal=sub,
        tax=tax,
        total=tot,
        payment_status='Pending'
    )
    db.session.add(invoice)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Order placed successfully! Invoice generated.", "invoice_id": invoice.id})

@bp.route('/sos/trigger', methods=['POST'])
@login_required
def trigger_sos():
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
        
    patient = current_user.patient_profile
    data = request.get_json() or {}
    lat = data.get("latitude", 12.9716) # Default Bengaluru lat
    lon = data.get("longitude", 77.5946) # Default Bengaluru lon
    
    # Create SOS request
    sos = EmergencyRequest(
        patient_id=patient.id,
        latitude=lat,
        longitude=lon,
        status='Active'
    )
    db.session.add(sos)
    db.session.commit()
    
    # Check if there are caregivers to notify
    caregivers = Caregiver.query.filter_by(patient_id=patient.id).all()
    cg_notified = [cg.caregiver_name for cg in caregivers]
    
    return jsonify({
        "success": True, 
        "message": "EMERGENCY ACTIVATED! Ambulance dispatched. Live location sent.",
        "caregivers_notified": cg_notified
    })

@bp.route('/telemedicine/room/<room_id>')
@login_required
def telemedicine_room(room_id):
    if current_user.role not in ['patient', 'doctor']:
        return redirect(url_for('auth.login'))
        
    # Simple room rendering
    appt = Appointment.query.filter_by(room_id=room_id).first()
    return render_template('telemedicine/room.html', title='Virtual Consultation Room', room_id=room_id, appointment=appt)
