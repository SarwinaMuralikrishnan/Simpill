from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, TimeField
from wtforms.validators import DataRequired, Length

class MedicineForm(FlaskForm):
    medicine_name = StringField('Medicine Name', validators=[DataRequired(), Length(max=100)])
    dosage = StringField('Dosage (e.g. 500mg)', validators=[DataRequired(), Length(max=50)])
    timing = SelectField('Timing', choices=[('Before food', 'Before food'), ('After food', 'After food')], validators=[DataRequired()])
    duration = SelectField('Duration (Days)', choices=[(str(i), f"{i} Days") for i in [1, 3, 5, 7, 10, 14, 30]], validators=[DataRequired()])
    reminders = SelectField('Reminders / Day', choices=[('1', '1 (Morning)'), ('2', '2 (Morning, Night)'), ('3', '3 (Morning, Afternoon, Night)')], validators=[DataRequired()])
    submit = SubmitField('Prescribe Medicine')

class DoctorProfileForm(FlaskForm):
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=100)])
    experience = IntegerField('Experience (Years)', validators=[DataRequired()])
    available_from = TimeField('Available From', validators=[DataRequired()])
    available_to = TimeField('Available To', validators=[DataRequired()])
    available_days = StringField('Available Days (e.g., Monday,Tuesday,Wednesday)', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Update Availability')
