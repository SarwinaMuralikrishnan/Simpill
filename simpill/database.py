import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simpill.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Read schema file and run it
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        
        conn = get_db_connection()
        try:
            conn.executescript(schema)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database schema initialization error: {e}")
        finally:
            conn.close()
    
    # Check if a default admin exists, if not, create one
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'Admin'")
    admin = cursor.fetchone()
    
    if not admin:
        default_admin_email = "admin@simpill.com"
        default_admin_pass = "admin123"
        hashed_pass = generate_password_hash(default_admin_pass)
        try:
            cursor.execute(
                "INSERT INTO users (full_name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                ("System Administrator", default_admin_email, "+1234567890", hashed_pass, "Admin")
            )
            conn.commit()
            print(f"Default admin created successfully: {default_admin_email} / {default_admin_pass}")
        except sqlite3.IntegrityError:
            pass
    conn.close()

def create_user(full_name, email, phone, password_hash, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (full_name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (full_name, email, phone, password_hash, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users(search_query=None, role_filter=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM users"
    conditions = []
    params = []
    
    if role_filter:
        conditions.append("role = ?")
        params.append(role_filter)
        
    if search_query:
        search_pattern = f"%{search_query}%"
        conditions.append("(full_name LIKE ? OR email LIKE ? OR phone LIKE ?)")
        params.extend([search_pattern, search_pattern, search_pattern])
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    conn.close()
    return users

def update_user(user_id, full_name, email, phone, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET full_name = ?, email = ?, phone = ?, role = ? WHERE id = ?",
            (full_name, email, phone, role, user_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_user_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total Users
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = cursor.fetchone()[0]
    
    # Total Patients
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Patient'")
    stats['total_patients'] = cursor.fetchone()[0]
    
    # Total Doctors
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Doctor'")
    stats['total_doctors'] = cursor.fetchone()[0]
    
    # Total Staff (Admin, Doctor, Receptionist, Lab Technician, Pharmacist, Cashier)
    # i.e., role != 'Patient'
    cursor.execute("SELECT COUNT(*) FROM users WHERE role != 'Patient'")
    stats['total_staff'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def get_patient_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()
    return profile

def create_or_update_patient(user_id, age, gender, address, blood_group, emergency_contact):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR REPLACE INTO patients (user_id, age, gender, address, blood_group, emergency_contact) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, age, gender, address, blood_group, emergency_contact)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error saving patient profile: {e}")
        return False
    finally:
        conn.close()

def submit_intake_form(patient_id, diagnosing_doctor, symptoms, health_problems, treatment_needs):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO intake_forms (patient_id, diagnosing_doctor, symptoms, health_problems, treatment_needs) 
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, diagnosing_doctor, symptoms, health_problems, treatment_needs)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error submitting intake form: {e}")
        return None
    finally:
        conn.close()

def get_patient_intake_forms(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM intake_forms WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
    forms = cursor.fetchall()
    conn.close()
    return forms

def add_medical_report(patient_id, file_name, file_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO medical_reports (patient_id, file_name, file_path) VALUES (?, ?, ?)",
            (patient_id, file_name, file_path)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding medical report: {e}")
        return None
    finally:
        conn.close()

def get_patient_medical_reports(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medical_reports WHERE patient_id = ? ORDER BY uploaded_at DESC", (patient_id,))
    reports = cursor.fetchall()
    conn.close()
    return reports

def create_appointment(patient_id, doctor_id, date, time, status='Scheduled'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO appointments (patient_id, doctor_id, date, time, status) VALUES (?, ?, ?, ?, ?)",
            (patient_id, doctor_id, date, time, status)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error creating appointment: {e}")
        return None
    finally:
        conn.close()

def get_appointments_detailed(date_filter=None, status_filter=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT a.*, p.full_name as patient_name, d.full_name as doctor_name 
        FROM appointments a
        JOIN users p ON a.patient_id = p.id
        JOIN users d ON a.doctor_id = d.id
    """
    conditions = []
    params = []
    
    if date_filter:
        conditions.append("a.date = ?")
        params.append(date_filter)
        
    if status_filter:
        conditions.append("a.status = ?")
        params.append(status_filter)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY a.date ASC, a.time ASC"
    
    cursor.execute(query, params)
    appointments = cursor.fetchall()
    conn.close()
    return appointments

def update_appointment_status(appointment_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (status, appointment_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating appointment status: {e}")
        return False
    finally:
        conn.close()

def get_doctors_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'Doctor' ORDER BY full_name ASC")
    doctors = cursor.fetchall()
    conn.close()
    return doctors

def get_patients_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'Patient' ORDER BY full_name ASC")
    patients = cursor.fetchall()
    conn.close()
    return patients

def get_patient_intake_by_id(intake_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT i.*, u.full_name as patient_name 
           FROM intake_forms i 
           JOIN users u ON i.patient_id = u.id 
           WHERE i.id = ?""",
        (intake_id,)
    )
    intake = cursor.fetchone()
    conn.close()
    return intake

def get_patient_intakes_all():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT i.*, u.full_name as patient_name 
           FROM intake_forms i 
           JOIN users u ON i.patient_id = u.id 
           ORDER BY i.created_at DESC"""
    )
    intakes = cursor.fetchall()
    conn.close()
    return intakes

def update_patient_intake_details(intake_id, diagnosing_doctor, symptoms, health_problems, treatment_needs):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE intake_forms 
               SET diagnosing_doctor = ?, symptoms = ?, health_problems = ?, treatment_needs = ? 
               WHERE id = ?""",
            (diagnosing_doctor, symptoms, health_problems, treatment_needs, intake_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating patient intake details: {e}")
        return False
    finally:
        conn.close()

def record_vitals(patient_id, recorded_by, blood_pressure, pulse, weight, temperature, oxygen_level):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO vitals (patient_id, recorded_by, blood_pressure, pulse, weight, temperature, oxygen_level) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (patient_id, recorded_by, blood_pressure, pulse, weight, temperature, oxygen_level)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error recording vitals: {e}")
        return None
    finally:
        conn.close()

def get_patient_vitals(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at DESC", (patient_id,))
    vitals = cursor.fetchall()
    conn.close()
    return vitals

def get_vitals_detailed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT v.*, p.full_name as patient_name, r.full_name as recorder_name 
           FROM vitals v 
           JOIN users p ON v.patient_id = p.id 
           LEFT JOIN users r ON v.recorded_by = r.id 
           ORDER BY v.recorded_at DESC"""
    )
    vitals = cursor.fetchall()
    conn.close()
    return vitals

def record_lab_result(patient_id, recorded_by, test_name, test_value, normal_range, comments):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO lab_results (patient_id, recorded_by, test_name, test_value, normal_range, comments) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (patient_id, recorded_by, test_name, test_value, normal_range, comments)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error recording lab result: {e}")
        return None
    finally:
        conn.close()

def get_patient_lab_results(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lab_results WHERE patient_id = ? ORDER BY recorded_at DESC", (patient_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_lab_results_detailed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT l.*, p.full_name as patient_name, r.full_name as recorder_name 
           FROM lab_results l 
           JOIN users p ON l.patient_id = p.id 
           LEFT JOIN users r ON l.recorded_by = r.id 
           ORDER BY l.recorded_at DESC"""
    )
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_uploaded_reports():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.*, p.full_name as patient_name 
           FROM medical_reports r 
           JOIN users p ON r.patient_id = p.id 
           ORDER BY r.uploaded_at DESC"""
    )
    reports = cursor.fetchall()
    conn.close()
    return reports

def create_prescription(patient_id, doctor_id, medicine_name, dosage, instructions):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO prescriptions (patient_id, doctor_id, medicine_name, dosage, instructions) 
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, doctor_id, medicine_name, dosage, instructions)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error creating prescription: {e}")
        return None
    finally:
        conn.close()

def get_patient_prescriptions(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT p.id, p.patient_id, p.doctor_id, p.medicine_name, p.dosage, p.instructions, p.status, p.created_at, d.full_name as doctor_name 
           FROM prescriptions p 
           JOIN users d ON p.doctor_id = d.id 
           WHERE p.patient_id = ? 
           ORDER BY p.created_at DESC""",
        (patient_id,)
    )
    prescriptions = cursor.fetchall()
    conn.close()
    return prescriptions

def get_all_prescriptions_detailed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT p.id, p.patient_id, p.doctor_id, p.medicine_name, p.dosage, p.instructions, p.status, p.created_at, pat.full_name as patient_name, doc.full_name as doctor_name 
           FROM prescriptions p 
           JOIN users pat ON p.patient_id = pat.id 
           JOIN users doc ON p.doctor_id = doc.id 
           ORDER BY p.created_at DESC"""
    )
    prescriptions = cursor.fetchall()
    conn.close()
    return prescriptions

def dispense_prescription(prescription_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE prescriptions SET status = 'Dispensed' WHERE id = ?",
            (prescription_id,)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error dispensing prescription: {e}")
        return False
    finally:
        conn.close()

def calculate_patient_charges(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Consultation Fee: Count appointments ($50.00 each)
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE patient_id = ?", (patient_id,))
    appt_count = cursor.fetchone()[0]
    consultation_fee = float(appt_count * 50.0)
    
    # 2. Lab Fee: Count lab results ($30.00 each)
    cursor.execute("SELECT COUNT(*) FROM lab_results WHERE patient_id = ?", (patient_id,))
    lab_count = cursor.fetchone()[0]
    lab_fee = float(lab_count * 30.0)
    
    # 3. Pharmacy Charges: Sum of dispensed medicines associated with this patient
    cursor.execute(
        """SELECT SUM(dm.quantity * m.price) 
           FROM dispensed_medicines dm
           JOIN medicines m ON dm.medicine_id = m.id
           JOIN prescriptions p ON dm.prescription_id = p.id
           WHERE p.patient_id = ?""",
        (patient_id,)
    )
    pharmacy_sum = cursor.fetchone()[0]
    pharmacy_charges = float(pharmacy_sum) if pharmacy_sum else 0.0
    
    total = consultation_fee + lab_fee + pharmacy_charges
    
    conn.close()
    return {
        'consultation_fee': consultation_fee,
        'lab_fee': lab_fee,
        'pharmacy_charges': pharmacy_charges,
        'total': total
    }

def create_bill(patient_id, consultation_fee, lab_fee, pharmacy_charges, amount, payment_method='Cash', status='Unpaid'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO bills (patient_id, consultation_fee, lab_fee, pharmacy_charges, amount, payment_method, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (patient_id, consultation_fee, lab_fee, pharmacy_charges, amount, payment_method, status)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error creating bill: {e}")
        return None
    finally:
        conn.close()

def get_patient_bills(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM bills WHERE patient_id = ? ORDER BY created_at DESC",
        (patient_id,)
    )
    bills = cursor.fetchall()
    conn.close()
    return bills

def get_all_bills_detailed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT b.*, p.full_name as patient_name 
           FROM bills b 
           JOIN users p ON b.patient_id = p.id 
           ORDER BY b.created_at DESC"""
    )
    bills = cursor.fetchall()
    conn.close()
    return bills

def pay_bill(bill_id, payment_method='Cash'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE bills SET status = 'Paid', payment_method = ? WHERE id = ?",
            (payment_method, bill_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error paying bill: {e}")
        return False
    finally:
        conn.close()

# --- Medicine Stock & Dispensing Operations ---

def add_medicine(name, quantity, expiry_date, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO medicines (name, quantity, expiry_date, price) VALUES (?, ?, ?, ?)",
            (name, quantity, expiry_date, price)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding medicine: {e}")
        return None
    finally:
        conn.close()

def update_medicine_stock(medicine_id, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE medicines SET quantity = ? WHERE id = ?",
            (quantity, medicine_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating stock: {e}")
        return False
    finally:
        conn.close()

def update_medicine_details(medicine_id, name, quantity, expiry_date, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE medicines SET name = ?, quantity = ?, expiry_date = ?, price = ? WHERE id = ?",
            (name, quantity, expiry_date, price, medicine_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating medicine details: {e}")
        return False
    finally:
        conn.close()

def get_all_medicines():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicines ORDER BY name ASC")
    medicines = cursor.fetchall()
    conn.close()
    return medicines

def get_medicine_by_id(medicine_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicines WHERE id = ?", (medicine_id,))
    medicine = cursor.fetchone()
    conn.close()
    return medicine

def get_medicine_by_name(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicines WHERE name = ?", (name,))
    medicine = cursor.fetchone()
    conn.close()
    return medicine

def get_low_stock_medicines(threshold=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicines WHERE quantity <= ? ORDER BY quantity ASC", (threshold,))
    medicines = cursor.fetchall()
    conn.close()
    return medicines

def dispense_prescription_stock(prescription_id, medicine_id, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check stock first
        cursor.execute("SELECT quantity FROM medicines WHERE id = ?", (medicine_id,))
        med = cursor.fetchone()
        if not med or med['quantity'] < quantity:
            return False, "Insufficient stock available."

        # Start transaction logic
        new_quantity = med['quantity'] - quantity
        cursor.execute("UPDATE medicines SET quantity = ? WHERE id = ?", (new_quantity, medicine_id))
        
        # Log to dispensed_medicines
        cursor.execute(
            "INSERT INTO dispensed_medicines (prescription_id, medicine_id, quantity) VALUES (?, ?, ?)",
            (prescription_id, medicine_id, quantity)
        )
        
        # Update prescription status
        cursor.execute("UPDATE prescriptions SET status = 'Dispensed' WHERE id = ?", (prescription_id,))
        
        conn.commit()
        return True, "Dispensed successfully."
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Transaction error during dispensing: {e}")
        return False, f"Database transaction error: {e}"
    finally:
        conn.close()

def get_dispensed_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT dm.*, m.name as medicine_name, p.medicine_name as prescribed_med, p.dosage,
                  pat.full_name as patient_name, doc.full_name as doctor_name
           FROM dispensed_medicines dm
           JOIN medicines m ON dm.medicine_id = m.id
           JOIN prescriptions p ON dm.prescription_id = p.id
           JOIN users pat ON p.patient_id = pat.id
           JOIN users doc ON p.doctor_id = doc.id
           ORDER BY dm.dispensed_at DESC"""
    )
    history = cursor.fetchall()
    conn.close()
    return history

# --- Relative Access Module Operations ---

def add_relative_relation(patient_id, relative_name, relative_email, relationship):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if the relative already has an account
        cursor.execute("SELECT id FROM users WHERE email = ?", (relative_email,))
        user = cursor.fetchone()
        
        if not user:
            # Auto-create relative user account
            from werkzeug.security import generate_password_hash
            default_pass = "relative123"
            hashed_pass = generate_password_hash(default_pass)
            cursor.execute(
                "INSERT INTO users (full_name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                (relative_name, relative_email, "Not provided", hashed_pass, "Relative")
            )
            relative_user_id = cursor.lastrowid
        else:
            relative_user_id = user['id']
            # Make sure their role is updated to Relative if they don't have a staff/clinical role
            cursor.execute("SELECT role FROM users WHERE id = ?", (relative_user_id,))
            current_role = cursor.fetchone()['role']
            if current_role == 'Patient':
                cursor.execute("UPDATE users SET role = 'Relative' WHERE id = ?", (relative_user_id,))
        
        # Link in relatives table
        cursor.execute(
            "INSERT INTO relatives (patient_id, relative_email, relationship) VALUES (?, ?, ?)",
            (patient_id, relative_email, relationship)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error adding relative relation: {e}")
        return False
    finally:
        conn.close()

def get_patient_relatives(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.id as relation_id, r.relative_email, r.relationship, r.created_at, u.full_name as relative_name
           FROM relatives r
           LEFT JOIN users u ON r.relative_email = u.email
           WHERE r.patient_id = ?
           ORDER BY r.created_at DESC""",
        (patient_id,)
    )
    relatives = cursor.fetchall()
    conn.close()
    return relatives

def get_relative_linked_patients(relative_email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.id, u.full_name, u.email, u.phone, r.relationship, r.id as relation_id
           FROM relatives r
           JOIN users u ON r.patient_id = u.id
           WHERE r.relative_email = ?
           ORDER BY r.created_at DESC""",
        (relative_email,)
    )
    patients = cursor.fetchall()
    conn.close()
    return patients

def delete_relative_relation(relation_id, patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM relatives WHERE id = ? AND patient_id = ?",
            (relation_id, patient_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting relative relation: {e}")
        return False
    finally:
        conn.close()

# --- Medicine Reminder Module Operations ---

def add_reminder(patient_id, medicine_name, dosage, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO reminders (patient_id, medicine_name, dosage, category) VALUES (?, ?, ?, ?)",
            (patient_id, medicine_name, dosage, category)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding reminder: {e}")
        return None
    finally:
        conn.close()

def update_reminder(reminder_id, medicine_name, dosage, category, patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE reminders SET medicine_name = ?, dosage = ?, category = ? WHERE id = ? AND patient_id = ?",
            (medicine_name, dosage, category, reminder_id, patient_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating reminder: {e}")
        return False
    finally:
        conn.close()

def delete_reminder(reminder_id, patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM reminders WHERE id = ? AND patient_id = ?",
            (reminder_id, patient_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting reminder: {e}")
        return False
    finally:
        conn.close()

def get_patient_reminders(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reminders WHERE patient_id = ? ORDER BY category ASC",
        (patient_id,)
    )
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def get_reminder_by_id(reminder_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
    reminder = cursor.fetchone()
    conn.close()
    return reminder

def mark_reminder_taken(reminder_id, taken_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO reminder_logs (reminder_id, taken_date) VALUES (?, ?)",
            (reminder_id, taken_date)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error marking reminder taken: {e}")
        return False
    finally:
        conn.close()

def get_today_reminder_status(patient_id, today_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.*, CASE WHEN rl.id IS NOT NULL THEN 1 ELSE 0 END as taken
           FROM reminders r
           LEFT JOIN reminder_logs rl ON r.id = rl.reminder_id AND rl.taken_date = ?
           WHERE r.patient_id = ?
           ORDER BY 
               CASE 
                   WHEN r.category LIKE 'Morning%' THEN 1
                   WHEN r.category LIKE 'Afternoon%' THEN 2
                   WHEN r.category LIKE 'Night%' THEN 3
                   ELSE 4
               END ASC, r.category ASC""",
        (today_date, patient_id)
    )
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def calculate_adherence_stats(patient_id):
    import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM reminders WHERE patient_id = ?", (patient_id,))
    reminders = cursor.fetchall()
    total_reminders = len(reminders)
    
    today_date = datetime.date.today().isoformat()
    
    # 1. Daily Adherence
    daily_taken = 0
    daily_pct = 0.0
    if total_reminders > 0:
        reminder_ids = [r['id'] for r in reminders]
        placeholders = ",".join("?" for _ in reminder_ids)
        cursor.execute(
            f"SELECT COUNT(*) FROM reminder_logs WHERE reminder_id IN ({placeholders}) AND taken_date = ?",
            (*reminder_ids, today_date)
        )
        daily_taken = cursor.fetchone()[0]
        daily_pct = (float(daily_taken) / float(total_reminders)) * 100.0
        
    # 2. Weekly Adherence (last 7 days including today)
    weekly_taken = 0
    weekly_pct = 0.0
    if total_reminders > 0:
        reminder_ids = [r['id'] for r in reminders]
        placeholders = ",".join("?" for _ in reminder_ids)
        
        last_7_dates = [(datetime.date.today() - datetime.timedelta(days=i)).isoformat() for i in range(7)]
        date_placeholders = ",".join("?" for _ in last_7_dates)
        
        cursor.execute(
            f"SELECT COUNT(*) FROM reminder_logs WHERE reminder_id IN ({placeholders}) AND taken_date IN ({date_placeholders})",
            (*reminder_ids, *last_7_dates)
        )
        weekly_taken = cursor.fetchone()[0]
        total_possible_doses = total_reminders * 7
        weekly_pct = (float(weekly_taken) / float(total_possible_doses)) * 100.0
        
    conn.close()
    return {
        'total_reminders': total_reminders,
        'daily_taken': daily_taken,
        'daily_adherence': round(daily_pct, 1),
        'weekly_taken': weekly_taken,
        'total_possible_weekly': total_reminders * 7,
        'weekly_adherence': round(weekly_pct, 1)
    }

# --- Reward Credit System Module Operations ---

def get_patient_wallet(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM wallet WHERE patient_id = ?", (patient_id,))
    wallet = cursor.fetchone()
    
    if not wallet:
        try:
            cursor.execute("INSERT INTO wallet (patient_id, credits, last_reward_date) VALUES (?, 0, NULL)", (patient_id,))
            conn.commit()
            cursor.execute("SELECT * FROM wallet WHERE patient_id = ?", (patient_id,))
            wallet = cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error creating patient wallet: {e}")
            
    conn.close()
    return wallet

def get_patient_reward_history(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reward_history WHERE patient_id = ? ORDER BY created_at DESC",
        (patient_id,)
    )
    history = cursor.fetchall()
    conn.close()
    return history

def get_weekly_completion_progress(patient_id):
    import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM reminders WHERE patient_id = ?", (patient_id,))
    reminders = cursor.fetchall()
    total_reminders = len(reminders)
    
    # Last 7 days progress list
    progress = []
    today = datetime.date.today()
    
    # Compile for the last 7 days (including today)
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        day_str = day.isoformat()
        day_name = day.strftime("%A")
        
        taken_count = 0
        completed = False
        
        if total_reminders > 0:
            reminder_ids = [r['id'] for r in reminders]
            placeholders = ",".join("?" for _ in reminder_ids)
            cursor.execute(
                f"SELECT COUNT(*) FROM reminder_logs WHERE reminder_id IN ({placeholders}) AND taken_date = ?",
                (*reminder_ids, day_str)
            )
            taken_count = cursor.fetchone()[0]
            completed = (taken_count == total_reminders)
            
        progress.append({
            'date': day_str,
            'day_name': day_name,
            'taken': taken_count,
            'total': total_reminders,
            'completed': completed
        })
        
    conn.close()
    # Return reversed order (oldest to newest day) for logical calendar view
    return list(reversed(progress))

def evaluate_weekly_reward(patient_id):
    import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get reminders count
    cursor.execute("SELECT id FROM reminders WHERE patient_id = ?", (patient_id,))
    reminders = cursor.fetchall()
    total_reminders = len(reminders)
    
    if total_reminders == 0:
        conn.close()
        return False, "Configure reminders to begin earning reward credits.", 0
        
    reminder_ids = [r['id'] for r in reminders]
    placeholders = ",".join("?" for _ in reminder_ids)
    
    # Evaluate last 7 days consecutive completion (today, today-1, ..., today-6)
    today = datetime.date.today()
    last_7_days = [today - datetime.timedelta(days=i) for i in range(7)]
    
    consecutive_days = 0
    for day in last_7_days:
        day_str = day.isoformat()
        cursor.execute(
            f"SELECT COUNT(*) FROM reminder_logs WHERE reminder_id IN ({placeholders}) AND taken_date = ?",
            (*reminder_ids, day_str)
        )
        taken_count = cursor.fetchone()[0]
        if taken_count == total_reminders:
            consecutive_days += 1
        else:
            break  # consecutive chain broke!
            
    # Grant reward condition check
    if consecutive_days < 7:
        conn.close()
        return False, f"Complete reminders consecutively. Progress: {consecutive_days}/7 days.", consecutive_days
        
    # Get wallet info
    cursor.execute("SELECT * FROM wallet WHERE patient_id = ?", (patient_id,))
    wallet = cursor.fetchone()
    if not wallet:
        cursor.execute("INSERT INTO wallet (patient_id, credits, last_reward_date) VALUES (?, 0, NULL)", (patient_id,))
        conn.commit()
        cursor.execute("SELECT * FROM wallet WHERE patient_id = ?", (patient_id,))
        wallet = cursor.fetchone()
        
    # Prevent claiming reward more than once within the last 7 days
    last_reward = wallet['last_reward_date']
    if last_reward:
        last_reward_dt = datetime.date.fromisoformat(last_reward)
        if (today - last_reward_dt).days < 7:
            conn.close()
            return False, "Wallet reward has already been claimed for this 7-day cycle.", consecutive_days
            
    # Perform wallet credit update
    new_credits = wallet['credits'] + 50
    today_str = today.isoformat()
    try:
        cursor.execute(
            "UPDATE wallet SET credits = ?, last_reward_date = ? WHERE patient_id = ?",
            (new_credits, today_str, patient_id)
        )
        cursor.execute(
            "INSERT INTO reward_history (patient_id, amount, reason) VALUES (?, 50, '7-Day Consecutive Reminder Completion')",
            (patient_id,)
        )
        conn.commit()
        return True, "Wallet successfully credited with +50 reward credits!", consecutive_days
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error granting reward: {e}")
        return False, "Database error during reward credits allocation.", consecutive_days
    finally:
        conn.close()

# --- Administrative Analytics Dashboard Operations ---

def get_admin_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Daily Patients: count of unique patients having checked-in appointments/logs for the last 7 days
    cursor.execute(
        """SELECT date, COUNT(DISTINCT patient_id) as count 
           FROM appointments 
           GROUP BY date 
           ORDER BY date DESC LIMIT 7"""
    )
    daily_patients = cursor.fetchall()
    daily_patients = list(reversed(daily_patients))
    
    # 2. Monthly Revenue: sum of paid bills grouped by month
    cursor.execute(
        """SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as revenue 
           FROM bills 
           WHERE status = 'Paid' 
           GROUP BY month 
           ORDER BY month DESC LIMIT 6"""
    )
    monthly_revenue = cursor.fetchall()
    monthly_revenue = list(reversed(monthly_revenue))
    
    # 3. Active Users: total users count grouped by role
    cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
    active_users = cursor.fetchall()
    
    # 4. Most Common Disease (Symptom): count of complaints
    cursor.execute("SELECT symptoms as symptom, COUNT(*) as count FROM intake_forms GROUP BY symptoms ORDER BY count DESC LIMIT 5")
    common_diseases = cursor.fetchall()
    
    # 5. Most Prescribed Medicine: count of prescriptions
    cursor.execute("SELECT medicine_name, COUNT(*) as count FROM prescriptions GROUP BY medicine_name ORDER BY count DESC LIMIT 5")
    common_medicines = cursor.fetchall()
    
    conn.close()
    return {
        'daily_patients': [{'date': row['date'], 'count': row['count']} for row in daily_patients],
        'monthly_revenue': [{'month': row['month'], 'revenue': row['revenue']} for row in monthly_revenue],
        'active_users': [{'role': row['role'], 'count': row['count']} for row in active_users],
        'common_diseases': [{'symptom': row['symptom'], 'count': row['count']} for row in common_diseases],
        'common_medicines': [{'medicine_name': row['medicine_name'], 'count': row['count']} for row in common_medicines]
    }

# --- AI Patient Health Report Synthesis ---

def generate_patient_ai_summary(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch latest intake symptoms
    cursor.execute("SELECT symptom, description, created_at FROM intake_forms WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1", (patient_id,))
    latest_intake = cursor.fetchone()
    
    # 2. Fetch latest vitals
    cursor.execute("SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at DESC LIMIT 1", (patient_id,))
    latest_vitals = cursor.fetchone()
    
    # 3. Fetch latest lab results
    cursor.execute("SELECT * FROM lab_results WHERE patient_id = ? ORDER BY recorded_at DESC LIMIT 3", (patient_id,))
    latest_labs = cursor.fetchall()
    
    # 4. Fetch active prescriptions
    cursor.execute("SELECT * FROM prescriptions WHERE patient_id = ?", (patient_id,))
    prescriptions = cursor.fetchall()
    
    # Compile symptoms description text
    s_text = ""
    if latest_intake:
        s_text = f"Patient presented reporting symptoms of '{latest_intake['symptom']}'. Note: {latest_intake['description']}."
    else:
        s_text = "No clinical intake symptoms logged recently."
        
    # Compile vitals description text
    v_text = ""
    if latest_vitals:
        bp = latest_vitals['blood_pressure']
        pulse = latest_vitals['pulse']
        temp = latest_vitals['temperature']
        spo2 = latest_vitals['oxygen_level']
        
        # Clinical interpretations
        bp_status = "Normal"
        try:
            sys, dia = map(int, bp.split('/'))
            if sys >= 130 or dia >= 80:
                bp_status = "Elevated"
            if sys >= 140 or dia >= 90:
                bp_status = "Stage 2 Hypertension"
        except:
            pass
            
        v_text = f"Vitals logs: BP is {bp} mmHg ({bp_status}), Heart Rate is {pulse} bpm, Temp is {temp}°C, SpO2 is {spo2}%."
    else:
        v_text = "No clinical vital signs recorded."
        
    # Compile lab results description text
    l_text = ""
    if latest_labs:
        items = []
        for lab in latest_labs:
            items.append(f"{lab['test_name']}: {lab['result_value']}")
        l_text = "Laboratory results filed: " + ", ".join(items) + "."
    else:
        l_text = "No diagnostic laboratory findings logged."
        
    # Compile prescriptions description text
    p_text = ""
    if prescriptions:
        items = []
        for rx in prescriptions:
            items.append(f"{rx['medicine_name']} ({rx['dosage']}, status: {rx['status']})")
        p_text = "Active pharmacotherapy: " + ", ".join(items) + "."
    else:
        p_text = "No active medicine prescriptions registered."
        
    # Markdown output text block
    summary_content = f"""### 1. Presenting Symptoms & Subjective History
{s_text}

### 2. Clinical Vitals Status
{v_text}

### 3. Laboratory Findings & Diagnostic Inputs
{l_text}

### 4. Prescribed Medication Therapy
{p_text}

### 5. AI Clinical Action Plan
* **Symptomatic Management**: Address primary complaint of {latest_intake['symptom'] if latest_intake else 'patient complaints'} by monitoring progress of {prescriptions[0]['medicine_name'] if prescriptions else 'medication therapy'}.
* **Adherence Audits**: Encourage consistency in medicine schedules reminders.
"""
    conn.close()
    return summary_content




