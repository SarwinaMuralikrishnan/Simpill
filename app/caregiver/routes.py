from flask import render_template, redirect, url_for, flash, request
from datetime import datetime, date
from app import db
from app.caregiver import bp
from app.models import Caregiver, Medicine, Reminder, EmergencyRequest, Appointment

@bp.route('/dashboard/<string:token>')
def dashboard(token):
    # Find caregiver by secure token
    caregiver = Caregiver.query.filter_by(token=token).first_or_404()
    patient = caregiver.patient
    
    # Update past pending reminders of today to 'Missed' for up-to-date compliance
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
    
    # Fetch today's reminders
    today_reminders = Reminder.query.join(Medicine).filter(
        Medicine.patient_id == patient.id,
        Reminder.date == today_date
    ).order_by(Reminder.reminder_time).all()
    
    taken_count = 0
    total_count = len(today_reminders)
    missed_count = 0
    
    for rem in today_reminders:
        if rem.status == 'Taken':
            taken_count += 1
        elif rem.status == 'Missed':
            missed_count += 1
            
    compliance = int((taken_count / total_count) * 100) if total_count > 0 else 100
    
    # Active medications
    medicines = Medicine.query.filter_by(patient_id=patient.id).all()
    
    # Conspicuous Missed Doses Alert list
    missed_alerts = [r for r in today_reminders if r.status == 'Missed']
    
    # SOS alert check
    active_sos = EmergencyRequest.query.filter_by(patient_id=patient.id, status='Active').first()
    
    # Fetch upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= today_date,
        Appointment.status.in_(['Approved', 'Scheduled'])
    ).all()
    
    return render_template(
        'caregiver/dashboard.html',
        title=f"Caregiver Portal: {patient.user.name}",
        caregiver=caregiver,
        patient=patient,
        today_reminders=today_reminders,
        compliance=compliance,
        taken_count=taken_count,
        total_count=total_count,
        missed_count=missed_count,
        medicines=medicines,
        missed_alerts=missed_alerts,
        active_sos=active_sos,
        upcoming_appointments=upcoming_appointments
    )
