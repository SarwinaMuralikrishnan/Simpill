from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app import db
from app.auth import bp
from app.forms.auth import LoginForm, SignupForm
from app.models import User, Patient, Doctor

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_role(current_user.role)
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            return redirect_role(user.role)
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect_role(current_user.role)
    
    form = SignupForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, phone=form.phone.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush() # To get user.id
        
        if user.role == 'patient':
            patient = Patient(user_id=user.id)
            db.session.add(patient)
        elif user.role == 'doctor':
            doctor = Doctor(user_id=user.id)
            db.session.add(doctor)
            
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/signup.html', title='Register', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

def redirect_role(role):
    if role == 'patient':
        return redirect(url_for('patient.dashboard'))
    elif role == 'doctor':
        return redirect(url_for('doctor.dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))
