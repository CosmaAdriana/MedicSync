"""
MedicSync — Global CSS injected on every page.
"""
import streamlit as st


def inject_global_css():
    st.markdown("""<style>

    /* ── Font — sistem local, fără request extern ─────────────────────── */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui,
                     sans-serif !important;
    }

    /* ── Page title ───────────────────────────────────────────────────── */
    h1 {
        font-size: 1.65rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.3px !important;
        margin-bottom: 0.1rem !important;
    }
    h2, h3 {
        font-weight: 600 !important;
        color: #1E293B !important;
    }

    /* ── Buttons ──────────────────────────────────────────────────────── */
    [data-testid="stBaseButton-primary"] button,
    [data-testid="stBaseButton-primary"] {
        background: #2563EB !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        letter-spacing: 0.01em !important;
        padding: 0.5rem 1.2rem !important;
        transition: background 0.15s !important;
    }
    [data-testid="stBaseButton-primary"]:hover {
        background: #1D4ED8 !important;
    }
    [data-testid="stBaseButton-secondary"] button,
    [data-testid="stBaseButton-secondary"] {
        border-radius: 8px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        border: 1px solid #CBD5E1 !important;
        color: #334155 !important;
    }
    [data-testid="stBaseButton-secondary"]:hover {
        background: #F1F5F9 !important;
        border-color: #94A3B8 !important;
    }

    /* ── Inputs ───────────────────────────────────────────────────────── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        border-radius: 8px !important;
        border-color: #CBD5E1 !important;
        font-size: 0.875rem !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    }

    /* ── Selectbox ────────────────────────────────────────────────────── */
    [data-testid="stSelectbox"] > div > div {
        border-radius: 8px !important;
        border-color: #CBD5E1 !important;
        font-size: 0.875rem !important;
    }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        border-bottom: 2px solid #E2E8F0 !important;
        gap: 0 !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: #64748B !important;
        padding: 0.6rem 1.1rem !important;
        border-radius: 6px 6px 0 0 !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: #2563EB !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #2563EB !important;
    }

    /* ── Metric cards ─────────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 1rem 1.2rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #64748B !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* ── Dataframe ────────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    /* ── Alerts / info boxes ──────────────────────────────────────────── */
    [data-testid="stAlert"] {
        border-radius: 8px !important;
        font-size: 0.875rem !important;
    }

    /* ── Sidebar refinements ──────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        border-right: 1px solid #E2E8F0 !important;
    }

    /* ── Divider ──────────────────────────────────────────────────────── */
    hr {
        border-color: #E2E8F0 !important;
        margin: 1rem 0 !important;
    }

    /* ── Hide "Press Enter to submit" tooltip ────────────────────────── */
    [data-testid="InputInstructions"] { display: none !important; }

    /* ── Hide Streamlit branding ──────────────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"] { visibility: hidden !important; }
    [data-testid="stDecoration"] { display: none !important; }

    </style>""", unsafe_allow_html=True)
