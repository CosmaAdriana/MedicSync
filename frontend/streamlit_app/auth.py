"""
MedicSync Frontend - Authentication & Authorization
Gestionează autentificarea utilizatorilor și session state.
"""
import os
import base64
import requests
import streamlit as st
from api_client import APIClient


@st.cache_data(show_spinner=False)
def _load_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _get_bg_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Preferă JPEG (mult mai mic), fallback la PNG
    for ext in ("poza4.jpg", "poza4.png"):
        p = os.path.join(root, ext)
        if os.path.exists(p):
            return p
    return os.path.join(root, "poza4.png")


def _inject_background():
    """Injectează imaginea de fundal poza4.png pe toată pagina."""
    bg_path = _get_bg_path()
    if not os.path.exists(bg_path):
        return
    img_b64 = _load_image_b64(bg_path)
    mime = "image/jpeg" if bg_path.endswith(".jpg") else "image/png"
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:{mime};base64,{img_b64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.52);
            z-index: 0;
        }}
        [data-testid="stHeader"] {{ background: transparent !important; }}
        [data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="stSidebarNav"] {{ display: none !important; }}
        [data-testid="collapsedControl"] {{ display: none !important; }}
        [data-testid="stVerticalBlock"] {{ position: relative; z-index: 1; }}
        .block-container {{ padding-top: 1rem !important; }}
        </style>
    """, unsafe_allow_html=True)


def _inject_form_glass_styles():
    """CSS pentru câmpurile de input și containerul formularului pe fundal întunecat."""
    st.markdown("""
        <style>
        /* Glass card pe stForm */
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.11) !important;
            backdrop-filter: blur(18px) !important;
            -webkit-backdrop-filter: blur(18px) !important;
            border: 1px solid rgba(255, 255, 255, 0.28) !important;
            border-radius: 20px !important;
            padding: 2rem 1.8rem 1.5rem 1.8rem !important;
        }
        /* Input fields */
        [data-testid="stTextInput"] input {
            background: rgba(255, 255, 255, 0.92) !important;
            color: #1a1a1a !important;
            border-color: rgba(255, 255, 255, 0.6) !important;
            border-radius: 8px !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: rgba(0, 0, 0, 0.35) !important;
        }
        [data-testid="stTextInput"] label,
        [data-testid="stSelectbox"] label {
            color: rgba(255, 255, 255, 0.92) !important;
            font-weight: 500 !important;
        }
        /* Selectbox */
        [data-testid="stSelectbox"] > div > div {
            background: rgba(255, 255, 255, 0.92) !important;
            color: #1a1a1a !important;
            border-color: rgba(255, 255, 255, 0.6) !important;
            border-radius: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "landing"  # "landing" | "login" | "register"


def landing_page():
    """Pagina de start cu background, info platformă și butoane login/register."""
    _inject_background()

    st.markdown("""
        <style>
        .feature-card {
            background: rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 16px;
            padding: 1.4rem 1rem;
            text-align: center;
            color: white;
            text-shadow: 0 1px 4px rgba(0,0,0,0.5);
            height: 100%;
        }
        .feature-card .fi { font-size: 2rem; margin-bottom: 0.5rem; }
        .feature-card h4 { font-size: 0.95rem; font-weight: 700; margin: 0 0 0.4rem 0; }
        .feature-card p  { font-size: 0.82rem; opacity: 0.85; margin: 0; line-height: 1.5; }
        </style>
    """, unsafe_allow_html=True)

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown("""
        <div style="
            text-align: center;
            color: white;
            text-shadow: 0 2px 14px rgba(0,0,0,0.85);
            padding: 6vh 0 3vh 0;
        ">
            <div style="font-size: 3.8rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0.3rem;">
                🏥 MedicSync
            </div>
            <div style="font-size: 1.35rem; opacity: 0.92; margin-bottom: 1rem;">
                Health 4.0 — Platforma Inteligentă pentru Spitale
            </div>
            <div style="
                font-size: 1rem; opacity: 0.75;
                max-width: 580px; margin: 0 auto 2.5rem auto; line-height: 1.7;
            ">
                Gestionează pacienții, inventarul și personalul medical dintr-un singur loc.<br>
                Decizii mai bune, mai rapid — cu ajutorul inteligenței artificiale.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Feature cards ─────────────────────────────────────────────────────────
    _, c1, c2, c3, c4, _ = st.columns([0.4, 1, 1, 1, 1, 0.4])
    features = [
        (c1, "👤", "Gestionare Pacienți",
         "Monitorizare completă, semne vitale și alerte clinice în timp real."),
        (c2, "🤖", "Predicții ML",
         "Algoritmi AI pentru necesarul de personal și stocurile de siguranță."),
        (c3, "📦", "Inventar FEFO",
         "Control automat al stocurilor cu alerte de expirare și reaprovizionare."),
        (c4, "🔗", "HL7 FHIR R4",
         "Interoperabilitate cu orice sistem medical prin standarde internaționale."),
    ]
    for col, icon, title, desc in features:
        col.markdown(f"""
            <div class="feature-card">
                <div class="fi">{icon}</div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CTA Buttons ───────────────────────────────────────────────────────────
    _, b1, _, b2, _ = st.columns([2.2, 1.1, 0.25, 1.1, 2.2])
    with b1:
        if st.button("🔐  Autentificare", use_container_width=True, type="primary", key="btn_go_login"):
            st.session_state.auth_view = "login"
            st.rerun()
    with b2:
        if st.button("📝  Înregistrare", use_container_width=True, key="btn_go_register"):
            st.session_state.auth_view = "register"
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
        <p style="
            position: fixed; bottom: 12px; right: 16px;
            color: rgba(255,255,255,0.4); font-size: 0.75rem; z-index: 999;
        ">🏥 MedicSync © 2026</p>
    """, unsafe_allow_html=True)


def login_page():
    """Formular de autentificare pe fundalul poza4, card transparent."""
    _inject_background()
    _inject_form_glass_styles()

    st.markdown("<div style='height: 7vh'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        if st.session_state.get("session_expired"):
            st.warning("⏳ Sesiunea ta a expirat. Te rugăm să te autentifici din nou.")
            st.session_state.session_expired = False

        st.markdown("""
            <div style="
                text-align: center; color: white;
                text-shadow: 0 1px 8px rgba(0,0,0,0.7);
                margin-bottom: 1.2rem;
            ">
                <div style="font-size: 1.9rem; font-weight: 700;">🔐 Autentificare</div>
                <div style="font-size: 0.95rem; opacity: 0.78; margin-top: 0.3rem;">
                    Intră în contul tău MedicSync
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="medic@spital.ro")
            password = st.text_input("Parolă", type="password", placeholder="••••••••")
            st.markdown("")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit = st.form_submit_button("🚀 Conectare", use_container_width=True, type="primary")
            with col_btn2:
                back = st.form_submit_button("◀️ Înapoi", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("⚠️ Completează email și parola!")
                else:
                    try:
                        import cache as _cache
                        api_client = st.session_state.api_client
                        api_client.login(email, password)
                        user = api_client.get_current_user()
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.auth_view = "landing"
                        # Pornește prefetch înainte de rerun — cache-ul e gata când se randează home
                        _cache.prefetch_all_async(api_client.token)
                        st.session_state.cache_warmed = True
                        st.rerun()
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 401:
                            st.error("❌ Email sau parolă incorectă!")
                        else:
                            st.error(f"❌ Eroare: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Eroare: {str(e)}")

            if back:
                st.session_state.auth_view = "landing"
                st.rerun()

    st.markdown("""
        <p style="
            position: fixed; bottom: 12px; right: 16px;
            color: rgba(255,255,255,0.4); font-size: 0.75rem; z-index: 999;
        ">🏥 MedicSync © 2026</p>
    """, unsafe_allow_html=True)


def register_page():
    """Formular de înregistrare pe fundalul poza4, card transparent."""
    _inject_background()
    _inject_form_glass_styles()

    st.markdown("<div style='height: 3vh'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("""
            <div style="
                text-align: center; color: white;
                text-shadow: 0 1px 8px rgba(0,0,0,0.7);
                margin-bottom: 1.2rem;
            ">
                <div style="font-size: 1.9rem; font-weight: 700;">📝 Înregistrare</div>
                <div style="font-size: 0.95rem; opacity: 0.78; margin-top: 0.3rem;">
                    Creează un cont nou în MedicSync
                </div>
            </div>
        """, unsafe_allow_html=True)

        role = st.selectbox(
            "Rol",
            options=["nurse", "doctor", "manager", "inventory_manager"],
            format_func=lambda x: {
                "nurse": "👨‍⚕️ Asistent Medical",
                "doctor": "🩺 Doctor",
                "manager": "👔 Manager",
                "inventory_manager": "📦 Manager Inventar"
            }[x],
            key="register_role"
        )

        dept_id = None
        if role in ("nurse", "doctor"):
            try:
                departments = st.session_state.api_client.get_departments()
                if departments:
                    dept_map = {d['name']: d['id'] for d in departments}
                    dept_select = st.selectbox(
                        "Secție / Departament *",
                        options=list(dept_map.keys()),
                        help="Selectează secția în care lucrezi",
                        key="register_dept"
                    )
                    dept_id = dept_map[dept_select]
            except Exception:
                st.warning("⚠️ Nu s-au putut încărca departamentele.")

        with st.form("register_form"):
            full_name = st.text_input("Nume Complet", placeholder="Dr. Ion Popescu")
            email = st.text_input("Email", placeholder="ion.popescu@spital.ro")
            password = st.text_input(
                "Parolă", type="password", placeholder="••••••••", help="Minim 6 caractere"
            )
            password_confirm = st.text_input("Confirmă Parola", type="password", placeholder="••••••••")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ Înregistrare", use_container_width=True, type="primary")
            with col2:
                back = st.form_submit_button("◀️ Înapoi", use_container_width=True)

            if submit:
                if not all([full_name, email, password, password_confirm]):
                    st.error("⚠️ Completează toate câmpurile!")
                elif password != password_confirm:
                    st.error("❌ Parolele nu se potrivesc!")
                elif len(password) < 6:
                    st.error("❌ Parola trebuie să aibă minim 6 caractere!")
                elif role in ("nurse", "doctor") and not dept_id:
                    st.error("⚠️ Selectează o secție!")
                else:
                    try:
                        api_client = st.session_state.api_client
                        result = api_client.register(full_name, email, password, role, dept_id)
                        st.success(f"✅ Cont creat cu succes pentru {result['full_name']}!")
                        api_client.login(email, password)
                        user = api_client.get_current_user()
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.auth_view = "landing"
                        st.balloons()
                        st.rerun()
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 409:
                            st.error("❌ Email-ul este deja înregistrat!")
                        else:
                            st.error(f"❌ Eroare la înregistrare: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Eroare: {str(e)}")

            if back:
                st.session_state.auth_view = "landing"
                st.rerun()

    st.markdown("""
        <p style="
            position: fixed; bottom: 12px; right: 16px;
            color: rgba(255,255,255,0.4); font-size: 0.75rem; z-index: 999;
        ">🏥 MedicSync © 2026</p>
    """, unsafe_allow_html=True)


def logout():
    """Clear session and logout user — revine la pagina landing."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.auth_view = "landing"
    st.session_state.cache_warmed = False
    st.session_state.pop("_sidebar_closed", None)
    st.session_state.api_client.clear_token()
    st.session_state.api_client = APIClient()
    st.rerun()


def force_logout_expired():
    """Deconectează utilizatorul când token-ul JWT expiră și afișează mesaj."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.auth_view = "login"
    st.session_state.session_expired = True
    st.session_state.cache_warmed = False
    st.session_state.api_client.clear_token()
    st.session_state.api_client = APIClient()
    st.rerun()


def handle_api_exception(e: Exception) -> bool:
    """
    Verifică dacă excepția e cauzată de sesiunea expirată.
    Dacă da, deconectează utilizatorul automat (nu revine — apelează st.rerun()).
    Returnează False dacă excepția e de alt tip.
    """
    from api_client import SessionExpiredException
    if isinstance(e, SessionExpiredException):
        force_logout_expired()
    return False


def require_auth(allowed_roles: list = None):
    """
    Require authentication for a page. Call at the top of each protected page.
    """
    init_session_state()
    if not st.session_state.authenticated:
        st.switch_page("app.py")

    if allowed_roles:
        user_role = st.session_state.user.get("role")
        if user_role not in allowed_roles:
            role_labels = {
                "nurse": "Asistent Medical",
                "doctor": "Doctor",
                "manager": "Manager",
                "inventory_manager": "Manager Inventar"
            }
            user_role_label = role_labels.get(user_role, user_role)
            st.markdown("""
                <div style="
                    text-align: center;
                    padding: 3rem 2rem;
                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                    border-radius: 16px;
                    border: 1px solid #dee2e6;
                    margin: 2rem auto;
                    max-width: 600px;
                ">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🔒</div>
                    <h2 style="color: #495057; margin-bottom: 0.5rem;">Secțiune restricționată</h2>
                    <p style="color: #6c757d; font-size: 1.1rem; margin-bottom: 1.5rem;">
                        Această secțiune nu este disponibilă pentru rolul tău.
                    </p>
                    <div style="
                        background: white;
                        border-radius: 8px;
                        padding: 1rem 1.5rem;
                        display: inline-block;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    ">
                        <span style="color: #868e96;">Rolul tău: </span>
                        <strong style="color: #212529;">""" + user_role_label + """</strong>
                    </div>
                    <p style="color: #adb5bd; font-size: 0.9rem; margin-top: 1.5rem;">
                        Dacă crezi că ar trebui să ai acces, contactează administratorul sistemului.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            st.stop()


def get_user_role() -> str:
    """Get current user's role."""
    if st.session_state.authenticated:
        return st.session_state.user.get("role")
    return None


def get_user_name() -> str:
    """Get current user's full name."""
    if st.session_state.authenticated:
        return st.session_state.user.get("full_name")
    return None
