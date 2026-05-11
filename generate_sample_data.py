"""
Generate realistic sample invoice data for the Finance Ops AI Dashboard.
Run this once to populate the data/ folder with CSV and PDF invoices.
"""

import csv
import os
import random
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

# ── Sample data pools ──────────────────────────────────────────────────────────

VENDORS = [
    {"name": "TechFlow Solutions",     "email": "billing@techflow.io",         "category": "Software"},
    {"name": "CloudBase Infrastructure","email": "accounts@cloudbase.com",      "category": "Infrastructure"},
    {"name": "DataSync Corp",          "email": "invoices@datasync.co",         "category": "Data Services"},
    {"name": "DesignStudio Pro",       "email": "finance@designstudio.pro",     "category": "Design"},
    {"name": "MarketMind Agency",      "email": "billing@marketmind.agency",    "category": "Marketing"},
    {"name": "LegalEagle Partners",    "email": "accounts@legaleagle.law",      "category": "Legal"},
    {"name": "OfficeSupply Direct",    "email": "orders@officesupply.com",      "category": "Office"},
    {"name": "SecureNet Systems",      "email": "billing@securenet.io",         "category": "Security"},
    {"name": "Talent Bridge",          "email": "finance@talentbridge.hr",      "category": "HR Services"},
    {"name": "Analytics Plus",         "email": "invoices@analyticsplus.co",    "category": "Analytics"},
]

DESCRIPTIONS = {
    "Software":        ["Monthly SaaS Subscription", "License Renewal", "API Usage Fees", "Software Development"],
    "Infrastructure":  ["Cloud Hosting — Monthly", "CDN Services", "Database Hosting", "Server Maintenance"],
    "Data Services":   ["Data Pipeline Processing", "ETL Services", "Data Storage", "Data Enrichment"],
    "Design":          ["Brand Design Services", "UI/UX Consulting", "Creative Assets", "Design Sprint"],
    "Marketing":       ["Digital Campaign Management", "SEO Services", "Content Creation", "Ad Spend Management"],
    "Legal":           ["Legal Consulting", "Contract Review", "Compliance Services", "IP Registration"],
    "Office":          ["Office Supplies Q2", "Printing Services", "Stationery Order", "Equipment Rental"],
    "Security":        ["Security Audit", "Penetration Testing", "SSL Certificates", "Compliance Monitoring"],
    "HR Services":     ["Recruitment Services", "Payroll Processing", "HR Consulting", "Training Programs"],
    "Analytics":       ["BI Dashboard Setup", "Monthly Analytics Report", "KPI Tracking", "Data Visualization"],
}

STATUSES = ["Paid", "Overdue", "Pending", "Disputed"]
STATUS_WEIGHTS = [0.40, 0.25, 0.28, 0.07]

TODAY = datetime.today()

def random_date(days_ago_min, days_ago_max):
    offset = random.randint(days_ago_min, days_ago_max)
    return TODAY - timedelta(days=offset)

def generate_invoice_row(i):
    vendor = random.choice(VENDORS)
    category = vendor["category"]
    desc = random.choice(DESCRIPTIONS[category])
    amount = round(random.uniform(500, 18000), 2)
    status = random.choices(STATUSES, STATUS_WEIGHTS)[0]

    if status == "Paid":
        issue_date = random_date(60, 120)
        due_date = issue_date + timedelta(days=30)
        paid_date = due_date - timedelta(days=random.randint(0, 5))
    elif status == "Overdue":
        issue_date = random_date(45, 90)
        due_date = issue_date + timedelta(days=30)
        paid_date = None
    elif status == "Pending":
        issue_date = random_date(1, 29)
        due_date = issue_date + timedelta(days=30)
        paid_date = None
    else:  # Disputed
        issue_date = random_date(20, 70)
        due_date = issue_date + timedelta(days=30)
        paid_date = None

    days_overdue = max(0, (TODAY - due_date).days) if status == "Overdue" else 0

    return {
        "invoice_id":   f"INV-{2024}-{i:04d}",
        "vendor_name":  vendor["name"],
        "vendor_email": vendor["email"],
        "category":     category,
        "description":  desc,
        "amount":       amount,
        "currency":     "EUR",
        "issue_date":   issue_date.strftime("%Y-%m-%d"),
        "due_date":     due_date.strftime("%Y-%m-%d"),
        "paid_date":    paid_date.strftime("%Y-%m-%d") if paid_date else "",
        "status":       status,
        "days_overdue": days_overdue,
        "notes":        "",
    }

# ── Generate CSV ───────────────────────────────────────────────────────────────

def generate_csv(n=40):
    rows = [generate_invoice_row(i + 1) for i in range(n)]
    path = "data/invoices.csv"
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅  Generated {n} invoices → {path}")
    return rows

# ── Generate PDF invoices ──────────────────────────────────────────────────────

def generate_pdf_invoice(row):
    filename = f"data/sample_invoices/{row['invoice_id']}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Normal"],
                                  fontSize=22, textColor=colors.HexColor("#1a1a2e"),
                                  spaceAfter=4)
    sub_style   = ParagraphStyle("Sub",   parent=styles["Normal"],
                                  fontSize=10, textColor=colors.HexColor("#6b7280"))
    label_style = ParagraphStyle("Label", parent=styles["Normal"],
                                  fontSize=9,  textColor=colors.HexColor("#6b7280"))
    value_style = ParagraphStyle("Value", parent=styles["Normal"],
                                  fontSize=10, textColor=colors.HexColor("#111827"))
    right_style = ParagraphStyle("Right", parent=styles["Normal"],
                                  fontSize=10, alignment=TA_RIGHT)

    elements = []

    # Header
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Paragraph(f"{row['invoice_id']}  ·  {row['issue_date']}", sub_style))
    elements.append(Spacer(1, 8*mm))

    # Vendor / Bill-to block
    info_data = [
        [Paragraph("FROM", label_style),  Paragraph("BILL TO", label_style)],
        [Paragraph(row["vendor_name"], value_style),
         Paragraph("Workfully S.L.", value_style)],
        [Paragraph(row["vendor_email"], sub_style),
         Paragraph("Barceloneta, Barcelona", sub_style)],
    ]
    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # Line items table
    header = ["Description", "Category", "Amount (EUR)"]
    line   = [row["description"], row["category"],
              f"€ {row['amount']:,.2f}"]
    items_data = [header, line,
                  ["", "TOTAL", f"€ {row['amount']:,.2f}"]]

    items_table = Table(items_data, colWidths=[95*mm, 45*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0),  (-1, 0),  colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",    (0, 0),  (-1, 0),  colors.white),
        ("FONTSIZE",     (0, 0),  (-1, 0),  9),
        ("FONTNAME",     (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("BOTTOMPADDING",(0, 0),  (-1, 0),  6),
        ("TOPPADDING",   (0, 0),  (-1, 0),  6),
        ("ALIGN",        (2, 0),  (2, -1),  "RIGHT"),
        ("FONTNAME",     (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND",   (0, -1), (-1, -1), colors.HexColor("#f3f4f6")),
        ("GRID",         (0, 0),  (-1, -2), 0.3, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS",(0,1), (-1,-2), [colors.white, colors.HexColor("#f9fafb")]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 8*mm))

    # Due date + status
    status_color = {
        "Paid": "#16a34a", "Overdue": "#dc2626",
        "Pending": "#d97706", "Disputed": "#7c3aed"
    }.get(row["status"], "#374151")

    meta_data = [
        [Paragraph("Due Date", label_style),
         Paragraph("Status", label_style),
         Paragraph("Payment Date", label_style)],
        [Paragraph(row["due_date"], value_style),
         Paragraph(f'<font color="{status_color}"><b>{row["status"]}</b></font>', value_style),
         Paragraph(row["paid_date"] or "—", value_style)],
    ]
    meta_table = Table(meta_data, colWidths=[57*mm, 57*mm, 57*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 12*mm))

    # Footer note
    elements.append(Paragraph(
        "This invoice was auto-processed by the Workfully Finance Ops AI system.",
        sub_style))

    doc.build(elements)

if __name__ == "__main__":
    os.makedirs("data/sample_invoices", exist_ok=True)
    rows = generate_csv(40)
    # Generate PDFs only for first 8 (to keep things fast)
    pdf_rows = [r for r in rows if r["status"] in ("Overdue", "Disputed")][:4] + \
               [r for r in rows if r["status"] == "Pending"][:2] + \
               [r for r in rows if r["status"] == "Paid"][:2]
    for row in pdf_rows:
        generate_pdf_invoice(row)
    print(f"✅  Generated {len(pdf_rows)} PDF invoices → data/sample_invoices/")
    print("\nDone! Run:  streamlit run app.py")
