from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, DateField, TimeField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length

class AppointmentForm(FlaskForm):
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    is_telemedicine = SelectField('Type', choices=[('0', 'Physical Consultation'), ('1', 'Virtual Telemedicine')], default='0')
    notes = TextAreaField('Notes')
    submit = SubmitField('Book Appointment')

class ReportUploadForm(FlaskForm):
    title = StringField('Report Title', validators=[DataRequired(), Length(max=100)])
    category = SelectField('Category', choices=[('Prescription', 'Prescription'), ('Report', 'Medical Report'), ('Medical Scan', 'Medical Scan')], validators=[DataRequired()])
    file = FileField('Report File (PDF, JPG, PNG)', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDFs and Images only!')
    ])
    submit = SubmitField('Upload Report')

class CaregiverForm(FlaskForm):
    caregiver_name = StringField('Caregiver Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    relation = StringField('Relation', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Add Caregiver')
