"""
data_loader.py
--------------
Handles loading, caching, and cleaning invoice data from CSV.
"""

import pandas as pd
import datetime
import os

REQUIRED_COLUMNS = [
    "invoice_id", "vendor_name", "vendor_email", "category",
    "description", "amount", "currency", "issue_date", "due_date",
    "paid_date", "status", "days_overdue", "notes"
]


def load_invoices(path: str = "data/invoices.csv") -> pd.DataFrame:
    """Load invoices CSV, validate, and compute derived fields."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = pd.read_csv(path, parse_dates=["issue_date", "due_date"])

    # Paid date may be empty
    df["paid_date"] = pd.to_datetime(df["paid_date"], errors="coerce")

    # Coerce amount
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

    # Re-compute days_overdue live
    today = pd.Timestamp(datetime.date.today())
    df["days_overdue"] = df.apply(
        lambda r: max(0, (today - r["due_date"]).days)
        if r["status"] == "Overdue" else 0,
        axis=1,
    )

    # Derived: month labels
    df["issue_month"] = df["issue_date"].dt.to_period("M").astype(str)

    return df


def append_invoice(new_row: dict, path: str = "data/invoices.csv") -> pd.DataFrame:
    """Append a newly extracted invoice to the CSV and return updated DataFrame."""
    df = load_invoices(path)

    # Avoid duplicates on invoice_id
    if new_row.get("invoice_id") in df["invoice_id"].values:
        return df

    new_df = pd.DataFrame([new_row])
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(path, index=False)
    return df


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Compute key KPIs for the dashboard header cards."""
    if df.empty:
        return {}

    total_invoices   = len(df)
    total_value      = df["amount"].sum()
    overdue_df       = df[df["status"] == "Overdue"]
    pending_df       = df[df["status"] == "Pending"]
    paid_df          = df[df["status"] == "Paid"]
    disputed_df      = df[df["status"] == "Disputed"]

    overdue_value    = overdue_df["amount"].sum()
    avg_days_overdue = overdue_df["days_overdue"].mean() if not overdue_df.empty else 0
    collection_rate  = len(paid_df) / total_invoices * 100 if total_invoices else 0

    return {
        "total_invoices":    total_invoices,
        "total_value":       total_value,
        "overdue_count":     len(overdue_df),
        "overdue_value":     overdue_value,
        "pending_count":     len(pending_df),
        "pending_value":     pending_df["amount"].sum(),
        "paid_count":        len(paid_df),
        "paid_value":        paid_df["amount"].sum(),
        "disputed_count":    len(disputed_df),
        "disputed_value":    disputed_df["amount"].sum(),
        "avg_days_overdue":  round(avg_days_overdue, 1),
        "collection_rate":   round(collection_rate, 1),
    }
