"""
MedicSync — Global CSS injected on every page.
Design: modern medical SaaS, teal accent, near-white canvas, Inter typography.
"""
import streamlit as st


def inject_global_css():
    st.markdown("""<style>

    /* ── Inter font ───────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Design tokens ────────────────────────────────────────────────── */
    :root {
        --accent:        oklch(61% 0.10 195);
        --accent-dim:    oklch(96% 0.025 195);
        --accent-dark:   oklch(49% 0.10 195);
        --canvas:        #f8fafc;
        --surface:       #ffffff;
        --border:        #e2e8f0;
        --border-strong: #cbd5e1;
        --text-1:        #0f172a;
        --text-2:        #475569;
        --text-3:        #94a3b8;
        --danger:        #dc2626;
        --danger-bg:     #fef2f2;
        --warn:          #d97706;
        --warn-bg:       #fffbeb;
        --ok:            #059669;
        --ok-bg:         #ecfdf5;
        --shadow-sm:     0 1px 3px rgba(15,23,42,0.05), 0 1px 2px rgba(15,23,42,0.04);
        --radius:        12px;
    }

    /* ── Font ─────────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI',
                     Helvetica, Arial, sans-serif !important;
    }

    /* ── Canvas ───────────────────────────────────────────────────────── */
    [data-testid="stAppViewContainer"],
    section.main {
        background: var(--canvas) !important;
    }

    /* ── Typography ───────────────────────────────────────────────────── */
    h1 {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        color: var(--text-1) !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 0.1rem !important;
        line-height: 1.2 !important;
    }
    h2 {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: var(--text-1) !important;
        letter-spacing: -0.3px !important;
    }
    h3, h4, h5 {
        font-weight: 600 !important;
        color: var(--text-1) !important;
    }
    p, li, span, label {
        color: var(--text-2);
    }

    /* ── Primary button — teal ────────────────────────────────────────── */
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-primary"] button {
        background: var(--accent) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        letter-spacing: 0.01em !important;
        padding: 0.5rem 1.2rem !important;
        transition: background 0.15s, box-shadow 0.15s !important;
        box-shadow: 0 1px 2px oklch(61% 0.10 195 / 0.25) !important;
    }
    [data-testid="stBaseButton-primary"]:hover {
        background: var(--accent-dark) !important;
    }

    /* ── Secondary button ─────────────────────────────────────────────── */
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-secondary"] button {
        background: var(--surface) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 8px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: var(--text-2) !important;
        transition: border-color 0.15s, color 0.15s !important;
    }
    [data-testid="stBaseButton-secondary"]:hover {
        border-color: var(--accent) !important;
        color: var(--text-1) !important;
        background: var(--accent-dim) !important;
    }

    /* ── Inputs ───────────────────────────────────────────────────────── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input {
        border-radius: 8px !important;
        border-color: var(--border-strong) !important;
        font-size: 0.875rem !important;
        background: var(--surface) !important;
        color: var(--text-1) !important;
        transition: border-color 0.15s, box-shadow 0.15s !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px oklch(61% 0.10 195 / 0.12) !important;
    }

    /* ── Textarea ─────────────────────────────────────────────────────── */
    [data-testid="stTextArea"] textarea {
        border-radius: 8px !important;
        border-color: var(--border-strong) !important;
        font-size: 0.875rem !important;
        background: var(--surface) !important;
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px oklch(61% 0.10 195 / 0.12) !important;
    }

    /* ── Selectbox ────────────────────────────────────────────────────── */
    [data-testid="stSelectbox"] > div > div {
        border-radius: 8px !important;
        border-color: var(--border-strong) !important;
        font-size: 0.875rem !important;
        background: var(--surface) !important;
    }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        border-bottom: 2px solid var(--border) !important;
        gap: 0 !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: var(--text-3) !important;
        padding: 0.6rem 1.1rem !important;
        border-radius: 6px 6px 0 0 !important;
        background: transparent !important;
        transition: color 0.15s !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        color: var(--text-1) !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--accent) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--accent) !important;
    }

    /* ── st.metric ────────────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: var(--shadow-sm) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        color: var(--text-1) !important;
        letter-spacing: -1.5px !important;
        line-height: 1 !important;
        font-variant-numeric: tabular-nums !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        color: var(--text-3) !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
        font-weight: 500 !important;
    }

    /* ── Dataframe ────────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ── Alerts ───────────────────────────────────────────────────────── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        font-size: 0.875rem !important;
    }

    /* ── Forms ────────────────────────────────────────────────────────── */
    [data-testid="stForm"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.5rem !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ── Expander ─────────────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        background: var(--surface) !important;
    }

    /* ── Divider ──────────────────────────────────────────────────────── */
    hr {
        border-color: var(--border) !important;
        margin: 1rem 0 !important;
    }

    /* ── Sidebar base ─────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }

    /* ── Caption / small text ─────────────────────────────────────────── */
    [data-testid="stCaptionContainer"] {
        color: var(--text-3) !important;
        font-size: 0.78rem !important;
    }

    /* ── Spinner ──────────────────────────────────────────────────────── */
    [data-testid="stSpinner"] {
        color: var(--accent) !important;
    }

    /* ── Hide Streamlit chrome ────────────────────────────────────────── */
    [data-testid="InputInstructions"] { display: none !important; }
    footer { visibility: hidden; }
    [data-testid="stHeader"]         { background: transparent !important; }
    [data-testid="stDecoration"]     { display: none !important; }
    [data-testid="stMainMenuPopover"]{ display: none !important; }
    [data-testid="stToolbarActions"] { visibility: hidden !important; }

    </style>""", unsafe_allow_html=True)
