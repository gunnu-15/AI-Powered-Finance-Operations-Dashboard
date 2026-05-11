# 💸 Finance Ops AI Dashboard

> An AI-powered finance operations tool that automates invoice tracking, overdue detection, and vendor follow-up email generation — built to simulate the finance engine of a lean early-stage startup.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/GPT--4o-Optional-green?logo=openai)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What This Does

This dashboard replaces the manual "invoice spreadsheet + email chase" workflow with a fully automated ops engine:

| Manual Work | This Tool |
|---|---|
| Scan inbox for unpaid invoices | Auto-flags overdue invoices from CSV |
| Chase vendors by hand | AI drafts follow-up emails graded by severity |
| Copy-paste invoice data | PDF extraction via GPT-4o or heuristics |
| Build status reports manually | Live KPI cards + 5 interactive charts |

**Designed for a 2-person finance team running lean operations** — the kind of setup at companies like TravelPerk, FreeNow, or any funded seed-stage startup.

---

## 🛠 Tech Stack

| Layer | Tool |
|---|---|
| Frontend / Dashboard | Streamlit |
| AI Extraction & Emails | OpenAI GPT-4o (optional) |
| PDF Parsing | pdfplumber |
| Charts | Plotly |
| Data | pandas + CSV |
| PDF Generation (samples) | ReportLab |

---

## 📦 Features

### 📊 Overview Tab
- **KPI Cards**: Total invoices, total value, overdue count/value, collection rate
- **Status Donut Chart**: Breakdown by Paid / Overdue / Pending / Disputed
- **Monthly Volume Bar Chart**: Stacked by status over time
- **Top Vendors Chart**: Horizontal bar of highest spend vendors
- **Overdue Risk Map**: Scatter plot — amount vs days overdue (bubble size = risk)
- **Category Spend**: Which categories drive the most invoice volume

### 📋 Invoice Ledger Tab
- Full searchable, filterable table with colour-coded status
- Export to CSV
- Overdue action list sorted by urgency

### 🤖 AI Follow-ups Tab
- One-click generation of follow-up emails for **all** overdue invoices
- Three severity tiers: **Gentle** (< 15d) → **Firm** (15–45d) → **Escalation** (45d+)
- GPT-4o mode: personalised, context-aware emails per vendor
- Offline mode: production-grade templates with the same tiering logic
- Copy-to-clipboard for subject and body

### 📤 Upload Invoice Tab
- Upload any PDF invoice
- GPT-4o extracts: vendor, amount, dates, description, status
- Offline fallback: regex heuristic parser
- Editable fields before adding to ledger
- Download sample PDF invoices

---

## 🚀 Quickstart

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/finance-ops-ai.git
cd finance-ops-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate sample data (40 invoices + 8 PDFs)
python generate_sample_data.py

# 4. Run the dashboard
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🔑 OpenAI Integration (Optional)

The dashboard works fully **without an API key** (offline mode):
- PDF parsing uses regex-based heuristics
- Emails use severity-graded templates

To enable GPT-4o:
1. Copy `.env.example` → `.env` and add your key, **or**
2. Paste your key directly in the sidebar API Key field at runtime

```bash
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-...
```

---

## 📁 Project Structure

```
finance-ops-ai/
├── app.py                      # Main Streamlit dashboard (4 tabs)
├── generate_sample_data.py     # Generates 40 invoices CSV + 8 PDF samples
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   ├── invoices.csv            # Auto-generated invoice ledger
│   └── sample_invoices/        # PDF invoice samples (auto-generated)
└── utils/
    ├── __init__.py
    ├── data_loader.py          # CSV I/O + KPI computation
    ├── invoice_extractor.py    # GPT-4o / heuristic PDF parser
    └── email_followup.py       # Email generation engine
```

---

## 💡 Business Context

> *"Most of it is already automated, your job is to operate it reliably: banking, invoice follow-up, coordinating with our gestor, payroll inputs, making sure nothing falls through the cracks."*  
> — Workfully JD

This project demonstrates exactly that philosophy:
- **Operate reliably**: automated daily-refresh of overdue status
- **Invoice follow-up**: AI drafts the emails, human approves and sends
- **Nothing falls through**: risk map + KPI cards surface everything at a glance
- **AI initiative support**: GPT-4o integration ready to extend to new workflows

---

## 📄 License

MIT — free to use, extend, and build upon.
