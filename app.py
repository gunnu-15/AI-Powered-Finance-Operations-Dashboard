"""
app.py  —  Workfully Finance Ops AI Dashboard
=============================================
Run with:  streamlit run app.py
"""

import os
import sys
import datetime
import tempfile

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Path setup ─────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from utils.data_loader        import load_invoices, get_summary_stats, append_invoice
from utils.invoice_extractor  import extract_invoice, compute_status
from utils.email_followup     import generate_followup_email, get_all_followups

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Ops AI · Workfully",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* ── Global background ── */
.stApp { background: #0f0f1a; color: #e8e8f0; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #13131f;
    border-right: 1px solid #1e1e35;
}
[data-testid="stSidebar"] .stMarkdown p { color: #9898b0; font-size: 0.82rem; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #16162a;
    border: 1px solid #1e1e35;
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="metric-container"] label { color: #7878a0 !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700; color: #e8e8f0; }
[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Buttons ── */
.stButton > button {
    background: #3b3bff;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.88rem;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s;
}
.stButton > button:hover { background: #5050ff; transform: translateY(-1px); }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    font-weight: 600;
    font-size: 0.88rem;
    color: #7878a0;
    border-radius: 8px 8px 0 0;
}
[data-testid="stTabs"] [aria-selected="true"] { color: #a0a0ff !important; }

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
}
.badge-overdue   { background: #3d0c0c; color: #f87171; }
.badge-pending   { background: #2d2000; color: #fbbf24; }
.badge-paid      { background: #0c2d1a; color: #4ade80; }
.badge-disputed  { background: #1e0a3c; color: #c084fc; }

/* ── Section headers ── */
.section-header {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #5050a0;
    margin: 0 0 10px 0;
}

/* ── Email card ── */
.email-card {
    background: #16162a;
    border: 1px solid #1e1e35;
    border-left: 3px solid #3b3bff;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    white-space: pre-wrap;
    color: #c8c8e0;
    line-height: 1.6;
}

/* ── Invoice upload zone ── */
[data-testid="stFileUploader"] {
    background: #13132a;
    border: 2px dashed #2a2a50 !important;
    border-radius: 12px;
    padding: 20px;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] { border-radius: 10px; border: none; }

/* ── Divider ── */
hr { border-color: #1e1e35; margin: 20px 0; }

/* ── Plotly charts transparent ── */
.js-plotly-plot .plotly { background: transparent !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────────
if "openai_client" not in st.session_state:
    st.session_state.openai_client = None
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💸 Finance Ops AI")
    st.markdown("*Workfully Internal Tool*")
    st.divider()

    # API Key input
    st.markdown('<p class="section-header">OpenAI Integration</p>', unsafe_allow_html=True)
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-… (optional)",
        help="Leave blank to use offline mode with template-based emails and heuristic PDF parsing.",
    )
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Quick validation
            client.models.list()
            st.session_state.openai_client = client
            st.session_state.api_key_set = True
            st.success("✅ GPT-4o connected")
        except Exception:
            st.error("❌ Invalid API key")
            st.session_state.openai_client = None
            st.session_state.api_key_set = False
    else:
        st.info("🔌 Offline mode — templates active")

    st.divider()

    # Filters
    st.markdown('<p class="section-header">Filters</p>', unsafe_allow_html=True)
    df_all = load_invoices()
    status_filter = st.multiselect(
        "Status",
        options=["Paid", "Overdue", "Pending", "Disputed"],
        default=["Paid", "Overdue", "Pending", "Disputed"],
    )
    if not df_all.empty:
        categories = sorted(df_all["category"].dropna().unique().tolist())
        cat_filter = st.multiselect("Category", options=categories, default=categories)
        amount_range = st.slider(
            "Amount (€)",
            min_value=0,
            max_value=int(df_all["amount"].max()) + 1000,
            value=(0, int(df_all["amount"].max()) + 1000),
            step=500,
        )
    else:
        cat_filter   = []
        amount_range = (0, 100000)

    st.divider()
    st.markdown(f"<p style='color:#5050a0;font-size:0.72rem;'>Last refreshed: {datetime.datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data"):
        st.rerun()


# ── Load + filter data ─────────────────────────────────────────────────────────
df = load_invoices()

if not df.empty:
    if status_filter:
        df = df[df["status"].isin(status_filter)]
    if cat_filter:
        df = df[df["category"].isin(cat_filter)]
    df = df[df["amount"].between(amount_range[0], amount_range[1])]

stats = get_summary_stats(load_invoices())  # always use full dataset for KPIs


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# Page title
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.markdown("# Finance Operations Dashboard")
    st.markdown(f"<p style='color:#5050a0;margin-top:-10px;'>Automated invoice tracking & AI follow-up engine · {datetime.date.today().strftime('%B %d, %Y')}</p>", unsafe_allow_html=True)
with col_badge:
    mode = "🤖 GPT-4o" if st.session_state.api_key_set else "🔌 Offline"
    st.markdown(f"<div style='text-align:right;margin-top:18px;'><span class='badge' style='background:#1a1a3a;color:#8080ff;font-size:0.8rem;padding:6px 16px;'>{mode} Mode</span></div>", unsafe_allow_html=True)

st.divider()

# ── KPI Cards ──────────────────────────────────────────────────────────────────
if stats:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📄 Total Invoices",  stats["total_invoices"])
    c2.metric("💶 Total Value",     f"€{stats['total_value']:,.0f}")
    c3.metric("🔴 Overdue",         f"{stats['overdue_count']} · €{stats['overdue_value']:,.0f}",
              delta=f"-{stats['avg_days_overdue']}d avg", delta_color="inverse")
    c4.metric("⏳ Pending",          f"{stats['pending_count']} · €{stats['pending_value']:,.0f}")
    c5.metric("✅ Collection Rate",  f"{stats['collection_rate']}%",
              delta=f"{stats['paid_count']} paid")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Overview",
    "📋  Invoice Ledger",
    "🤖  AI Follow-ups",
    "📤  Upload Invoice",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overview / Analytics
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if df.empty:
        st.info("No invoice data yet. Run `python generate_sample_data.py` to populate.")
    else:
        CHART_BG    = "rgba(0,0,0,0)"
        CHART_FONT  = "#9898b0"
        GRID_COLOR  = "#1e1e35"
        STATUS_COLORS = {
            "Paid": "#4ade80", "Overdue": "#f87171",
            "Pending": "#fbbf24", "Disputed": "#c084fc"
        }

        chart_defaults = dict(
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(color=CHART_FONT, family="DM Sans"),
            margin=dict(l=20, r=20, t=40, b=20),
        )

        row1_l, row1_r = st.columns([1, 1])

        # ── Donut: Status breakdown ────────────────────────────────────────────
        with row1_l:
            st.markdown('<p class="section-header">Invoice Status Breakdown</p>', unsafe_allow_html=True)
            status_grp = df.groupby("status")["amount"].sum().reset_index()
            fig_donut = go.Figure(go.Pie(
                labels=status_grp["status"],
                values=status_grp["amount"],
                hole=0.6,
                marker_colors=[STATUS_COLORS.get(s, "#6b7280") for s in status_grp["status"]],
                textfont_size=12,
                hovertemplate="<b>%{label}</b><br>€%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_donut.update_layout(
                **chart_defaults,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                annotations=[dict(text=f"€{df['amount'].sum():,.0f}", x=0.5, y=0.5,
                                  font_size=16, font_color="#e8e8f0", showarrow=False)],
                height=300,
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

        # ── Bar: Monthly invoice volume ────────────────────────────────────────
        with row1_r:
            st.markdown('<p class="section-header">Monthly Invoice Volume</p>', unsafe_allow_html=True)
            monthly = df.groupby(["issue_month", "status"])["amount"].sum().reset_index()
            fig_bar = px.bar(
                monthly,
                x="issue_month",
                y="amount",
                color="status",
                color_discrete_map=STATUS_COLORS,
                barmode="stack",
                labels={"amount": "Amount (€)", "issue_month": "Month"},
            )
            fig_bar.update_layout(**chart_defaults, height=300,
                xaxis=dict(gridcolor=GRID_COLOR, tickangle=-30),
                yaxis=dict(gridcolor=GRID_COLOR, tickprefix="€"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

        row2_l, row2_r = st.columns([1, 1])

        # ── Bar: Top vendors by amount ─────────────────────────────────────────
        with row2_l:
            st.markdown('<p class="section-header">Top Vendors by Invoice Value</p>', unsafe_allow_html=True)
            vendor_grp = (df.groupby("vendor_name")["amount"]
                           .sum()
                           .sort_values(ascending=True)
                           .tail(8)
                           .reset_index())
            fig_vendor = px.bar(
                vendor_grp,
                x="amount",
                y="vendor_name",
                orientation="h",
                color="amount",
                color_continuous_scale=[[0, "#1a1a4a"], [0.5, "#3b3bff"], [1, "#a0a0ff"]],
                labels={"amount": "Total (€)", "vendor_name": "Vendor"},
            )
            fig_vendor.update_layout(**chart_defaults, height=300,
                xaxis=dict(gridcolor=GRID_COLOR, tickprefix="€"),
                yaxis=dict(gridcolor=GRID_COLOR),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_vendor, use_container_width=True, config={"displayModeBar": False})

        # ── Scatter: Days overdue vs amount ────────────────────────────────────
        with row2_r:
            st.markdown('<p class="section-header">Overdue Risk Map</p>', unsafe_allow_html=True)
            overdue_df = load_invoices()
            overdue_df = overdue_df[overdue_df["status"] == "Overdue"]
            if overdue_df.empty:
                st.info("No overdue invoices. 🎉")
            else:
                fig_scatter = px.scatter(
                    overdue_df,
                    x="days_overdue",
                    y="amount",
                    size="amount",
                    color="days_overdue",
                    hover_name="vendor_name",
                    hover_data={"invoice_id": True, "days_overdue": True, "amount": ":.2f"},
                    color_continuous_scale=[[0, "#fbbf24"], [0.5, "#f97316"], [1, "#dc2626"]],
                    labels={"days_overdue": "Days Overdue", "amount": "Amount (€)"},
                    size_max=40,
                )
                fig_scatter.update_layout(**chart_defaults, height=300,
                    xaxis=dict(gridcolor=GRID_COLOR),
                    yaxis=dict(gridcolor=GRID_COLOR, tickprefix="€"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})

        # ── Category pie ───────────────────────────────────────────────────────
        st.markdown('<p class="section-header">Spend by Category</p>', unsafe_allow_html=True)
        cat_grp = df.groupby("category")["amount"].sum().reset_index()
        fig_cat = px.bar(
            cat_grp.sort_values("amount", ascending=False),
            x="category",
            y="amount",
            color="amount",
            color_continuous_scale=[[0, "#1a1a4a"], [1, "#6060ff"]],
            labels={"amount": "Total (€)", "category": "Category"},
        )
        fig_cat.update_layout(**chart_defaults, height=250,
            xaxis=dict(gridcolor=GRID_COLOR),
            yaxis=dict(gridcolor=GRID_COLOR, tickprefix="€"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Invoice Ledger
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-header">All Invoices</p>', unsafe_allow_html=True)

    if df.empty:
        st.info("No invoices to display with current filters.")
    else:
        # Colour-coded status column
        def colour_status(val):
            colours = {
                "Overdue":  "color:#f87171;font-weight:700",
                "Pending":  "color:#fbbf24;font-weight:600",
                "Paid":     "color:#4ade80;font-weight:600",
                "Disputed": "color:#c084fc;font-weight:700",
            }
            return colours.get(val, "")

        display_cols = ["invoice_id", "vendor_name", "category", "description",
                        "amount", "issue_date", "due_date", "status", "days_overdue"]

        display_df = df[display_cols].copy()
        display_df["amount"]     = display_df["amount"].map(lambda x: f"€{x:,.2f}")
        display_df["issue_date"] = display_df["issue_date"].dt.strftime("%Y-%m-%d")
        display_df["due_date"]   = display_df["due_date"].dt.strftime("%Y-%m-%d")
        display_df.columns       = ["Invoice ID", "Vendor", "Category", "Description",
                                    "Amount", "Issued", "Due", "Status", "Days Overdue"]

        styled = display_df.style.map(colour_status, subset=["Status"])

        st.dataframe(styled, use_container_width=True, height=480)

        # Download
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button(
            "⬇️  Export as CSV",
            data=csv_bytes,
            file_name=f"invoices_{datetime.date.today()}.csv",
            mime="text/csv",
        )

        # Overdue summary table
        overdue_view = load_invoices()
        overdue_view = overdue_view[overdue_view["status"] == "Overdue"].sort_values("days_overdue", ascending=False)
        if not overdue_view.empty:
            st.divider()
            st.markdown('<p class="section-header">🔴 Overdue — Action Required</p>', unsafe_allow_html=True)
            ov_cols = ["invoice_id", "vendor_name", "amount", "due_date", "days_overdue"]
            ov_df = overdue_view[ov_cols].copy()
            ov_df["amount"]     = ov_df["amount"].map(lambda x: f"€{x:,.2f}")
            ov_df["due_date"]   = pd.to_datetime(ov_df["due_date"]).dt.strftime("%Y-%m-%d")
            ov_df.columns       = ["Invoice ID", "Vendor", "Amount", "Due Date", "Days Overdue"]
            st.dataframe(ov_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI Follow-ups
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    full_df = load_invoices()
    overdue_invoices = full_df[full_df["status"] == "Overdue"]
    n_overdue = len(overdue_invoices)

    st.markdown(f'<p class="section-header">AI-Generated Follow-up Emails · {n_overdue} Overdue Invoice{"s" if n_overdue != 1 else ""}</p>', unsafe_allow_html=True)

    if n_overdue == 0:
        st.success("🎉 No overdue invoices. All caught up!")
    else:
        if st.session_state.api_key_set:
            st.info("🤖 GPT-4o will personalise each email based on vendor, amount, and overdue duration.")
        else:
            st.info("🔌 Offline mode: Using smart templates graded by overdue severity. Add an OpenAI API key to enable GPT-4o personalisation.")

        if st.button("⚡ Generate All Follow-up Emails"):
            with st.spinner("Generating emails…"):
                emails = get_all_followups(full_df, st.session_state.openai_client)
                st.session_state["generated_emails"] = emails

        if "generated_emails" in st.session_state:
            emails = st.session_state["generated_emails"]
            st.markdown(f"**{len(emails)} emails ready to send:**")

            for email in emails:
                days = email["days_overdue"]
                border = "#dc2626" if days > 45 else "#f97316" if days > 20 else "#fbbf24"

                with st.expander(f"📧 {email['vendor_name']} · {email['invoice_id']} · **{days} days overdue**"):
                    col_meta, col_tone = st.columns([3, 1])
                    with col_meta:
                        st.markdown(f"**To:** {email.get('vendor_email', 'N/A')}")
                        st.markdown(f"**Amount:** €{email['amount']:,.2f}")
                    with col_tone:
                        tone_colors = {"Gentle": "🟡", "Firm": "🟠", "Escalation": "🔴", "AI-generated": "🤖"}
                        st.markdown(f"**Tone:** {tone_colors.get(email['tone'], '📝')} {email['tone']}")
                        st.markdown(f"**Method:** {email['method']}")

                    st.markdown(f"**Subject:** `{email['subject']}`")
                    st.markdown(f"<div class='email-card'>{email['body']}</div>", unsafe_allow_html=True)

                    btn_col1, btn_col2 = st.columns([1, 4])
                    with btn_col1:
                        if st.button("📋 Copy Subject", key=f"copy_sub_{email['invoice_id']}"):
                            st.code(email['subject'])
                    with btn_col2:
                        if st.button("📋 Copy Body", key=f"copy_body_{email['invoice_id']}"):
                            st.code(email['body'])

        # Individual email generator
        st.divider()
        st.markdown('<p class="section-header">Generate Single Follow-up</p>', unsafe_allow_html=True)
        selected_inv = st.selectbox(
            "Select overdue invoice",
            options=overdue_invoices["invoice_id"].tolist(),
        )
        if selected_inv:
            row = overdue_invoices[overdue_invoices["invoice_id"] == selected_inv].iloc[0]
            if st.button("Generate Email for This Invoice"):
                with st.spinner("Generating…"):
                    email = generate_followup_email(
                        invoice_id=row["invoice_id"],
                        vendor_name=row["vendor_name"],
                        description=row["description"],
                        amount=float(row["amount"]),
                        currency=row.get("currency", "EUR"),
                        due_date=str(row["due_date"].date()),
                        days_overdue=int(row["days_overdue"]),
                        openai_client=st.session_state.openai_client,
                    )
                st.markdown(f"**Subject:** `{email['subject']}`")
                st.markdown(f"<div class='email-card'>{email['body']}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Upload Invoice
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-header">Upload & Extract Invoice (PDF)</p>', unsafe_allow_html=True)
    st.markdown("Upload any PDF invoice — the AI engine will extract key fields automatically and add it to the ledger.")

    uploaded = st.file_uploader("Drop a PDF invoice here", type=["pdf"])

    if uploaded is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        st.info(f"📄 File received: **{uploaded.name}** ({uploaded.size // 1024} KB)")

        if st.button("🔍 Extract Invoice Data"):
            with st.spinner("Extracting data from PDF…"):
                extracted = extract_invoice(tmp_path, st.session_state.openai_client)

            st.success("✅ Extraction complete!")
            st.markdown('<p class="section-header">Extracted Fields</p>', unsafe_allow_html=True)

            # Editable fields
            col_l, col_r = st.columns(2)
            with col_l:
                inv_id     = st.text_input("Invoice ID",    value=extracted.get("invoice_id", ""))
                vendor     = st.text_input("Vendor Name",   value=extracted.get("vendor_name", ""))
                v_email    = st.text_input("Vendor Email",  value=extracted.get("vendor_email", ""))
                category   = st.text_input("Category",      value=extracted.get("category", ""))
            with col_r:
                desc       = st.text_input("Description",   value=extracted.get("description", ""))
                amount     = st.number_input("Amount (€)",  value=float(extracted.get("amount", 0) or 0), min_value=0.0)
                issue_date = st.text_input("Issue Date (YYYY-MM-DD)", value=str(extracted.get("issue_date", "")))
                due_date   = st.text_input("Due Date (YYYY-MM-DD)",   value=str(extracted.get("due_date", "")))

            status_opts = ["Pending", "Overdue", "Paid", "Disputed"]
            det_status  = extracted.get("status", "Pending")
            status_idx  = status_opts.index(det_status) if det_status in status_opts else 0
            status      = st.selectbox("Status", status_opts, index=status_idx)

            st.markdown(f"*Extraction method: **{extracted.get('extraction_method', 'heuristic')}***")

            if st.button("➕ Add to Ledger"):
                new_row = {
                    "invoice_id":   inv_id,
                    "vendor_name":  vendor,
                    "vendor_email": v_email,
                    "category":     category,
                    "description":  desc,
                    "amount":       amount,
                    "currency":     "EUR",
                    "issue_date":   issue_date,
                    "due_date":     due_date,
                    "paid_date":    "",
                    "status":       status,
                    "days_overdue": 0,
                    "notes":        "",
                }
                append_invoice(new_row)
                st.success(f"✅ Invoice **{inv_id}** added to the ledger.")
                st.rerun()

        os.unlink(tmp_path)

    st.divider()
    st.markdown('<p class="section-header">Sample PDF Invoices</p>', unsafe_allow_html=True)
    sample_dir = "data/sample_invoices"
    if os.path.exists(sample_dir):
        pdfs = [f for f in os.listdir(sample_dir) if f.endswith(".pdf")]
        if pdfs:
            st.markdown(f"**{len(pdfs)} sample invoices available** in `data/sample_invoices/`")
            for pdf in sorted(pdfs)[:5]:
                with open(os.path.join(sample_dir, pdf), "rb") as f:
                    st.download_button(
                        f"⬇️  {pdf}",
                        data=f.read(),
                        file_name=pdf,
                        mime="application/pdf",
                        key=f"dl_{pdf}",
                    )
        else:
            st.info("Run `python generate_sample_data.py` to create sample PDFs.")
    else:
        st.info("Run `python generate_sample_data.py` to create sample PDFs.")
