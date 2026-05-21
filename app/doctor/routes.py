from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, time, timedelta
import json
import os
import secrets
from werkzeug.utils import secure_filename
from app import db
from app.doctor import bp
from app.models import (
    User, Patient, Doctor, Appointment, Medicine, Reminder, 
    Report, Caregiver, InventoryItem, LabTestBooking, Invoice, EmergencyRequest
)
from app.forms.doctor import MedicineForm, DoctorProfileForm
from app.services.analyzer_service import analyze_report_text
from app.services.pdf_service import generate_lab_report_pdf

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'doctor':
        return redirect(url_for('auth.login'))
        
    doctor = current_user.doctor_profile
    
    # 1. Total Patients under this doctor (patients who have scheduled appointments)
    patient_ids = [a.patient_id for a in Appointment.query.filter_by(doctor_id=doctor.id).all()]
    total_patients_count = len(set(patient_ids))
    
    # 2. Today's Appointments Count
    today = date.today()
    today_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date == today
    ).order_by(Appointment.time).all()
    today_appts_count = len(today_appts)
    
    # 3. Active prescriptions (medicines overall in system)
    active_prescriptions = Medicine.query.count()
    
    # 4. Pending Emergency Requests (Global notification indicator)
    active_emergencies = EmergencyRequest.query.filter_by(status='Active').all()
    
    # 5. Pending approvals list
    pending_approvals = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status='Pending'
    ).order_by(Appointment.date, Appointment.time).all()
    
    # 6. Low stock items count (Pharmacy alerts widget)
    low_stock_count = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.low_stock_threshold).count()
    
    return render_template(
        'doctor/dashboard.html', 
        title='Doctor Dashboard',
        total_patients=total_patients_count,
        today_appts_count=today_appts_count,
        active_prescriptions=active_prescriptions,
        pending_approvals=pending_approvals,
        today_appts=today_appts,
        active_emergencies=active_emergencies,
        low_stock_count=low_stock_count
    )

@bp.route('/appointments/approve/<int:appt_id>', methods=['POST'])
@login_required
def approve_appointment(appt_id):
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
        
    appt = Appointment.query.get_or_404(appt_id)
    if appt.doctor_id != current_user.doctor_profile.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    appt.status = 'Approved'
    db.session.commit()
    flash('Appointment approved successfully!', 'success')
    return redirect(url_for('doctor.dashboard'))

@bp.route('/appointments/reject/<int:appt_id>', methods=['POST'])
@login_required
def reject_appointment(appt_id):
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
        
    appt = Appointment.query.get_or_404(appt_id)
    if appt.doctor_id != current_user.doctor_profile.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    appt.status = 'Cancelled'
    db.session.commit()
    flash('Appointment declined.', 'success')
    return redirect(url_for('doctor.dashboard'))

@bp.route('/patients')
@login_required
def patients():
    if current_user.role != 'doctor':
        return redirect(url_for('auth.login'))
        
    # List all patients in the system
    all_patients = Patient.query.all()
    return render_template('doctor/patients.html', title='Patients Directory', patients=all_patients)

@bp.route('/patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def patient_detail(patient_id):
    if current_user.role != 'doctor':
        return redirect(url_for('auth.login'))
        
    patient = Patient.query.get_or_404(patient_id)
    medicines = Medicine.query.filter_by(patient_id=patient.id).all()
    reports = Report.query.filter_by(patient_id=patient.id).order_by(Report.upload_date.desc()).all()
    lab_bookings = LabTestBooking.query.filter_by(patient_id=patient.id).order_by(LabTestBooking.booking_date.desc()).all()
    invoices = Invoice.query.filter_by(patient_id=patient.id).order_by(Invoice.created_at.desc()).all()
    
    # Calculate patient adherence rate
    today = date.today()
    total_reminders = Reminder.query.join(Medicine).filter(
        Medicine.patient_id == patient.id,
        Reminder.date <= today
    ).count()
    taken_reminders = Reminder.query.join(Medicine).filter(
        Medicine.patient_id == patient.id,
        Reminder.date <= today,
        Reminder.status == 'Taken'
    ).count()
    adherence_rate = int((taken_reminders / total_reminders) * 100) if total_reminders > 0 else 100
    
    return render_template(
        'doctor/patient_detail.html', 
        title=f"Patient: {patient.user.name}",
        patient=patient,
        medicines=medicines,
        reports=reports,
        lab_bookings=lab_bookings,
        invoices=invoices,
        adherence_rate=adherence_rate
    )

@bp.route('/patient/<int:patient_id>/prescribe', methods=['GET', 'POST'])
@login_required
def prescribe(patient_id):
    if current_user.role != 'doctor':
        return redirect(url_for('auth.login'))
        
    patient = Patient.query.get_or_404(patient_id)
    form = MedicineForm()
    
    if form.validate_on_submit():
        medicine = Medicine(
            patient_id=patient.id,
            medicine_name=form.medicine_name.data,
            dosage=form.dosage.data,
            timing=form.timing.data,
            duration=f"{form.duration.data} Days"
        )
        db.session.add(medicine)
        db.session.flush() # To get medicine.id
        
        # Auto populate reminder logs
        duration_days = int(form.duration.data)
        reminders_per_day = int(form.reminders.data)
        
        # Map time targets
        time_slots = []
        if reminders_per_day == 1:
            time_slots = [time(8, 0)] # Morning
        elif reminders_per_day == 2:
            time_slots = [time(8, 0), time(20, 0)] # Morning, Night
        elif reminders_per_day == 3:
            time_slots = [time(8, 0), time(13, 0), time(20, 0)] # Morning, Afternoon, Night
            
        start_date = date.today()
        for day_offset in range(duration_days):
            current_day = start_date + timedelta(days=day_offset)
            for t_slot in time_slots:
                reminder = Reminder(
                    medicine_id=medicine.id,
                    reminder_time=t_slot,
                    status='Pending',
                    date=current_day
                )
                db.session.add(reminder)
                
        db.session.commit()
        flash(f'Prescription for {medicine.medicine_name} created. Reminders generated.', 'success')
        return redirect(url_for('doctor.patient_detail', patient_id=patient.id))
        
    return render_template('doctor/prescribe.html', title='Prescribe Medication', form=form, patient=patient)

@bp.route('/availability', methods=['GET', 'POST'])
@login_required
def availability():
    if current_user.role != 'doctor':
        return redirect(url_for('auth.login'))
        
    doctor = current_user.doctor_profile
    form = DoctorProfileForm(obj=doctor)
    
    if form.validate_on_submit():
        doctor.specialization = form.specialization.data
        doctor.experience = form.experience.data
        doctor.available_from = form.available_from.data
        doctor.available_to = form.available_to.data
        doctor.available_days = form.available_days.data
        
        db.session.commit()
        flash('Doctor profile and availability updated successfully!', 'success')
        return redirect(url_for('doctor.dashboard'))
        
    return render_template('doctor/availability.html', title='Edit Availability', form=form)

@bp.route('/pharmacy', methods=['GET', 'POST'])
@login_required
def pharmacy():
    if current_user.role != 'doctor':
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        # Add stock item
        name = request.form.get('name')
        qty = int(request.form.get('quantity', 0))
        price = float(request.form.get('price', 0.0))
        expiry = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()
        barcode = request.form.get('barcode', None)
        low_stock = int(request.form.get('low_stock_threshold', 10))
        
        # Check if already exists, else create
        item = InventoryItem.query.filter_by(name=name).first()
        if item:
            item.quantity += qty
            item.price = price
            item.expiry_date = expiry
            if barcode:
                item.barcode = barcode
        else:
            item = InventoryItem(
                name=name,
                quantity=qty,
                price=price,
                expiry_date=expiry,
                barcode=barcode,
                low_stock_threshold=low_stock
            )
            db.session.add(item)
            
        db.session.commit()
        flash(f'Inventory for {name} updated!', 'success')
        return redirect(url_for('doctor.pharmacy'))
        
    inventory = InventoryItem.query.all()
    return render_template('doctor/pharmacy.html', title='Pharmacy Inventory Management', inventory=inventory)

@bp.route('/laboratory', methods=['GET', 'POST'])
@login_required
def laboratory():
    if current_user.role != 'doctor':
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        # Complete lab test booking, upload result PDF, and generate AI insights
        booking_id = int(request.form.get('booking_id'))
        booking = LabTestBooking.query.get_or_404(booking_id)
        
        raw_result_text = request.form.get('raw_result')
        
        # Analyze using service
        analysis = analyze_report_text(raw_result_text)
        
        # Save results explanation
        booking.status = 'Completed'
        booking.result_explanation = analysis["summary"]
        
        # Generate official PDF Report
        filename = f"lab_report_{booking.id}_{secrets.token_hex(4)}.pdf"
        output_dir = os.path.join(current_app.static_folder, 'uploads/lab_reports')
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, filename)
        
        generate_lab_report_pdf(
            patient_name=booking.patient.user.name,
            test_name=booking.test_name,
            date_str=booking.booking_date.strftime('%Y-%m-%d'),
            status='Completed',
            findings_list=analysis["abnormal_findings"] + analysis["normal_findings"],
            explanation=analysis["summary"],
            output_path=pdf_path
        )
        
        booking.result_pdf = f"uploads/lab_reports/{filename}"
        db.session.commit()
        flash(f'Lab Test {booking.test_name} completed. PDF report compiled!', 'success')
        return redirect(url_for('doctor.laboratory'))
        
    bookings = LabTestBooking.query.order_by(LabTestBooking.booking_date.desc()).all()
    return render_template('doctor/laboratory.html', title='Lab Booking Requests', bookings=bookings)

@bp.route('/sos/resolve/<int:sos_id>', methods=['POST'])
@login_required
def resolve_sos(sos_id):
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
        
    sos = EmergencyRequest.query.get_or_404(sos_id)
    sos.status = 'Resolved'
    db.session.commit()
    flash('Emergency resolved.', 'success')
    return redirect(url_for('doctor.dashboard'))
