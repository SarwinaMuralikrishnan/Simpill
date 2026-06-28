# Walkthrough: SimPill – Phase 6: Doctor, Pharmacist, and Cashier Portals

This walkthrough summarizes the final implementation of the **Doctor**, **Pharmacist**, and **Cashier** dashboards, completing the entire operations loop of the SimPill system. The code resides in `C:\Users\Lenovo\Desktop\simpill` and is synchronized with the persistent scratch folder.

## Final Folder Structure
```text
simpill/
├── app.py                      # Core server routes (setup upload folders, role check guards, full operational endpoints)
├── database.py                 # SQLite interface (CRUD for appointments, vitals, test results, prescriptions, billing)
├── requirements.txt            # Python requirements (Flask, Flask-Login)
├── schema.sql                  # Database schema (declares users, patients, intake_forms, reports, appointments, vitals, lab_results, prescriptions, billing)
├── simpill.db                  # Database storage file (updated with new schemas)
├── static/
│   ├── css/
│   │   └── style.css           # Premium custom styles (neon medical gradients, glassmorphism, responsive sidebar)
│   ├── js/
│   │   └── main.js             # Client utilities (deletion prompts, auto-hide alerts, password toggles)
│   └── uploads/                # Directory containing uploaded patient clinical PDF, JPG, and PNG documents
└── templates/
    ├── base.html               # Main navbar layout and global flashes
    ├── welcome.html            # Landing page
    ├── login.html              # Login form
    ├── signup.html             # Account registration (allows selecting all roles for testing)
    ├── dashboard.html          # Fallback general dashboard
    ├── patient/
    │   ├── dashboard.html      # Patient portal dashboard (profile, history, reports, active prescriptions, invoices)
    │   ├── edit_profile.html   # Patient demographic profile customization form
    │   └── intake.html         # Medical intake form
    ├── reception/
    │   ├── dashboard.html      # Receptionist console (Today's schedule, Queue, registry, intakes)
    │   ├── register_patient.html # Walk-in Patient registration form
    │   ├── edit_intake.html    # Patient intake details editor form
    │   └── schedule.html       # Appointment booking form
    ├── lab_tech/
    │   ├── dashboard.html      # Lab Tech dashboard (Patient registry, reports, symptoms, vitals registry, tests log)
    │   ├── record_vitals.html  # Vital signs recording form
    │   ├── upload_results.html # Lab test findings upload form
    │   └── patient_history.html # Combined patient diagnostics history view
    ├── doctor/
    │   ├── dashboard.html      # Doctor console (Consultation queue, Patients registry, write prescriptions)
    │   └── prescribe.html      # Medication prescription writing form
    ├── pharmacist/
    │   └── dashboard.html      # Pharmacist dashboard (Pending prescriptions list, Dispensed drug log)
    └── cashier/
        ├── dashboard.html      # Cashier dashboard (Open unpaid invoices, paid transaction receipts log)
        └── create_bill.html    # Billing invoice generation form
```

---

## Key Completed Features (Phase 6)

1. **Prescriptions & Billing Tables**:
   - Built the `prescriptions` table storing patient, doctor, medication name, dosage frequency, instructions, and dispense status (`Pending` or `Dispensed`).
   - Built the `billing` table storing patient, description, bill amount, and payment status (`Unpaid` or `Paid`).

2. **Doctor Portal**:
   - Lists today's consultations scheduled with the logged-in physician.
   - Allows doctors to write a prescription with a form select mapping to the patient directory.
   - Restricts access via the `@doctor_required` decorator.

3. **Pharmacist Portal**:
   - Renders a list of all active prescriptions.
   - Single-click action "Dispense" updates status in the database to mark medication order completed.
   - Restricts access via the `@pharmacist_required` decorator.

4. **Cashier Portal**:
   - Renders open unpaid bills and compiles paid receipts logs.
   - Allows cashier staff to generate new patient invoices specifying amount values and description notes.
   - Single-click action "Collect Payment" marks the invoice as Paid in the database.
   - Restricts access via the `@cashier_required` decorator.

5. **Integrated Patient Review**:
   - The **Patient Dashboard** was updated to fetch prescriptions and bills.
   - Shows active prescriptions (indicating if pending prepared or already dispensed) and outstanding invoices.

---

## Verification & Manual Testing Plan

### 1. Run the Flask Dev Server
Start the Flask engine:
```powershell
cd C:\Users\Lenovo\Desktop\simpill
python app.py
```

### 2. Clinical Operations Walkthrough Checklist
- [ ] **Doctor Prescribe**: Log in as a Doctor. Navigate to the registry, select a patient, and write a prescription (e.g. `Metformin 500mg`, dosage `Twice daily`). Submit and verify it records in the database.
- [ ] **Pharmacist Dispense**: Log in as a Pharmacist. Confirm the pending prescription shows up on your dashboard. Click **Dispense** and check that it transfers to the Dispensed Log tab.
- [ ] **Cashier Invoice**: Log in as a Cashier. Click **Generate Invoice** and bill the patient `$120.00` for a consult and diagnostics checks. Submit and verify it shows up in the Open Invoices tab.
- [ ] **Patient Review**: Log in as the patient. Confirm that both your Metformin prescription (marked as `Dispensed`) and the `$120.00` invoice (marked as `Unpaid`) appear in your dashboard widgets.
- [ ] **Cashier Checkout**: Log back in as a Cashier. Click **Collect Payment** next to the patient's bill. Confirm it marks as paid and transfers to the Transaction Log. Check the patient dashboard again to confirm the status is updated to `Paid`.
