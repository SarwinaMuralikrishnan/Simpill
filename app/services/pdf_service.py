from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os

def generate_lab_report_pdf(patient_name, test_name, date_str, status, findings_list, explanation, output_path):
    """
    Generates a structured PDF for lab test results using ReportLab.
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # 1. Header
    c.setFillColor(colors.HexColor("#1e3a8a")) # Deep blue
    c.rect(0, height - 80, width, 80, stroke=0, fill=1)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, height - 48, "SIMPILL AI ECOSYSTEM")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 64, "Laboratory Report and Automated Diagnostic Insights")
    
    # Date and Status
    c.drawRightString(width - 40, height - 48, f"Date: {date_str}")
    c.drawRightString(width - 40, height - 64, f"Status: {status.upper()}")
    
    # 2. Patient & Test Details Block
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.rect(40, height - 170, width - 80, 70, stroke=1, fill=1)
    
    c.setFillColor(colors.HexColor("#0f172a")) # Slate dark
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 120, "PATIENT NAME:")
    c.setFont("Helvetica", 11)
    c.drawString(160, height - 120, patient_name)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 140, "LABORATORY TEST:")
    c.setFont("Helvetica", 11)
    c.drawString(160, height - 140, test_name)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 160, "DOCUMENT TYPE:")
    c.setFont("Helvetica", 11)
    c.drawString(160, height - 160, "Official Laboratory Examination Report")
    
    # 3. Findings Table
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 200, "1. BIOMARKER CLINICAL FINDINGS")
    
    # Table Header
    y = height - 230
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.rect(40, y - 5, width - 80, 20, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Biomarker")
    c.drawString(180, y, "Observed Value")
    c.drawString(300, y, "Reference Range")
    c.drawString(430, y, "Diagnostic Status")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#0f172a"))
    
    for item in findings_list:
        y -= 22
        # Draw row line
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.setLineWidth(0.5)
        c.line(40, y - 5, width - 40, y - 5)
        
        c.drawString(50, y, item.get("marker", ""))
        c.drawString(180, y, f"{item.get('value', '')} {item.get('unit', '')}")
        c.drawString(300, y, f"{item.get('reference', '')} {item.get('unit', '')}")
        
        status_label = item.get("status", "Normal")
        if status_label == "Normal":
            c.setFillColor(colors.HexColor("#15803d")) # Green
        else:
            c.setFillColor(colors.HexColor("#b91c1c")) # Red
        c.drawString(430, y, status_label)
        c.setFillColor(colors.HexColor("#0f172a")) # Reset color
        
    # 4. AI Insights Block
    y -= 40
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "2. AI DIAGNOSTIC REPORT EXPLANATION")
    
    y -= 15
    c.setFillColor(colors.HexColor("#f0fdf4")) # Soft green tint bg
    c.setStrokeColor(colors.HexColor("#bbf7d0"))
    c.rect(40, y - 160, width - 80, 150, stroke=1, fill=1)
    
    c.setFillColor(colors.HexColor("#166534"))
    c.setFont("Helvetica-Oblique", 9.5)
    
    # Text Wrapping for explanation
    text_object = c.beginText(50, y - 20)
    text_object.setLeading(14)
    
    # Wrap text manually at ~80 characters
    words = explanation.split()
    lines = []
    current_line = []
    for word in words:
        if len(" ".join(current_line + [word])) < 85:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
        
    for line in lines[:10]: # Draw max 10 lines
        text_object.textLine(line)
    c.drawText(text_object)
    
    # 5. Footer Signature
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont("Helvetica", 9)
    c.drawString(40, 50, "Generated automatically by SimPill AI Ecosystem. Verified Diagnostic Document.")
    c.drawRightString(width - 40, 50, "Signature: SimPill AI Lab")
    
    c.showPage()
    c.save()
