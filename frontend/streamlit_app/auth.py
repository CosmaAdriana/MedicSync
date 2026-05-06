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
        /* Hide "Press Enter to submit" */
        [data-testid="InputInstructions"] { display: none !important; }
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

    # Gradient overlay mai fin peste cel plat din _inject_background
    st.markdown("""<style>
        [data-testid="stAppViewContainer"]::before {
            background: linear-gradient(
                180deg,
                rgba(5, 15, 35, 0.92) 0%,
                rgba(5, 15, 35, 0.68) 40%,
                rgba(5, 15, 35, 0.62) 68%,
                rgba(5, 15, 35, 0.88) 100%
            ) !important;
        }
    </style>""", unsafe_allow_html=True)

    # ── Hero — wordmark ──────────────────────────────────────────────────────
    st.markdown("""<div style="text-align:center;padding-top:7vh;font-family:'Inter',system-ui,sans-serif;">
<div style="margin-bottom:2.2rem;display:inline-block;"><svg width="228" height="54" viewBox="0 0 228 54" xmlns="http://www.w3.org/2000/svg"><rect width="54" height="54" rx="13" fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.2)" stroke-width="1"/><polyline points="7,27 15,27 19,14 27,40 32,19 37,27 47,27" fill="none" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/><text y="38" font-family="Inter,system-ui,sans-serif" font-size="28"><tspan x="66" font-weight="800" fill="white" letter-spacing="-0.5">Medic</tspan><tspan font-weight="400" fill="rgba(255,255,255,0.46)" letter-spacing="-0.2">Sync</tspan></text></svg>
<p style="font-size:0.62rem;letter-spacing:4px;text-transform:uppercase;color:rgba(255,255,255,0.24);margin:6px 0 0;font-weight:500;">Health 4.0</p></div></div>""", unsafe_allow_html=True)

    # ── Hero — tagline + descriere ────────────────────────────────────────────
    st.markdown("""<div style="text-align:center;padding:0 1rem 3rem;font-family:'Inter',system-ui,sans-serif;">
<h1 style="font-size:3.6rem;font-weight:800;color:white;letter-spacing:-2px;line-height:1.08;margin:0 0 1.2rem;">Spitalul tău,<br>digitalizat complet.</h1>
<p style="font-size:1.05rem;color:rgba(255,255,255,0.55);max-width:500px;margin:0 auto 0.5rem;line-height:1.8;">Pacienți, inventar și personal medical — dintr-un singur loc.<br>Predicții AI, alerte în timp real și standarde HL7 FHIR R4.</p>
</div>""", unsafe_allow_html=True)

    # ── CTA Buttons ───────────────────────────────────────────────────────────
    _, b1, _, b2, _ = st.columns([2.5, 1, 0.2, 1, 2.5])
    with b1:
        if st.button("Autentificare", use_container_width=True, type="primary", key="btn_go_login"):
            st.session_state.auth_view = "login"
            st.rerun()
    with b2:
        if st.button("Înregistrare", use_container_width=True, key="btn_go_register"):
            st.session_state.auth_view = "register"
            st.rerun()

    st.markdown("<div style='height:2.8rem'></div>", unsafe_allow_html=True)

    # ── Feature cards ─────────────────────────────────────────────────────────
    _S = 'xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4a9db3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
    _fi_user = f'<svg {_S}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
    _fi_bot  = f'<svg {_S}><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>'
    _fi_pkg  = f'<svg {_S}><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>'
    _fi_link = f'<svg {_S}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'

    features = [
        (_fi_user, "Gestionare Pacienți",
         "Monitorizare completă cu semne vitale, alerte clinice automate și actualizare status în timp real."),
        (_fi_bot,  "Predicții ML",
         "RandomForest pentru necesarul de personal și stocuri — predicții pe 7 și 30 de zile."),
        (_fi_pkg,  "Inventar FEFO",
         "Alerte de expirare, reaprovizionare automată la livrare și consum monitorizat per secție."),
        (_fi_link, "HL7 FHIR R4",
         "Export nativ pentru interoperabilitate cu orice sistem medical sau platformă națională."),
    ]

    _, c1, c2, c3, c4, _ = st.columns([0.35, 1, 1, 1, 1, 0.35])
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], features):
        col.markdown(f"""
        <div style="
            background: rgba(5, 15, 35, 0.52);
            backdrop-filter: blur(20px) saturate(150%);
            -webkit-backdrop-filter: blur(20px) saturate(150%);
            border: 1px solid rgba(255,255,255,0.08);
            border-top: 2px solid #4a9db3;
            border-radius: 16px;
            padding: 1.5rem 1.1rem 1.4rem;
            text-align: center;
            height: 100%;
            font-family: 'Inter', system-ui, sans-serif;
        ">
            <div style="margin-bottom: 0.85rem; opacity: 0.85;">{icon}</div>
            <h4 style="
                color: white;
                font-size: 0.88rem;
                font-weight: 700;
                margin: 0 0 0.5rem;
                letter-spacing: -0.2px;
            ">{title}</h4>
            <p style="
                color: rgba(255,255,255,0.46);
                font-size: 0.80rem;
                line-height: 1.65;
                margin: 0;
            ">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
        <p style="
            position: fixed; bottom: 14px; right: 18px;
            color: rgba(255,255,255,0.22);
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            z-index: 999;
        ">MedicSync &copy; 2026</p>
    """, unsafe_allow_html=True)


def login_page():
    """Formular de autentificare pe fundalul poza4, card transparent."""
    _inject_background()
    _inject_form_glass_styles()

    main = st.empty()

    with main.container():
        st.markdown("<div style='height: 7vh'></div>", unsafe_allow_html=True)

        _, col, _ = st.columns([1, 1.3, 1])
        with col:
            if st.session_state.get("session_expired"):
                st.warning("Sesiunea ta a expirat. Te rugăm să te autentifici din nou.")
                st.session_state.session_expired = False

            st.markdown("""
                <div style="
                    text-align: center; color: white;
                    text-shadow: 0 1px 8px rgba(0,0,0,0.7);
                    margin-bottom: 1.2rem;
                ">
                    <div style="font-size: 1.9rem; font-weight: 700;">Autentificare</div>
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
                    submit = st.form_submit_button("Conectare", use_container_width=True, type="primary")
                with col_btn2:
                    back = st.form_submit_button("Înapoi", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Completează email și parola!")
                    else:
                        try:
                            import cache as _cache
                            api_client = st.session_state.api_client
                            api_client.login(email, password)
                            user = api_client.get_current_user()
                            st.session_state.authenticated = True
                            st.session_state.user = user
                            st.session_state.auth_view = "landing"
                            _cache.prefetch_all_async(api_client.token)
                            st.session_state.cache_warmed = True
                            main.empty()
                            st.rerun()
                        except requests.exceptions.HTTPError as e:
                            if e.response.status_code == 401:
                                st.error("Email sau parolă incorectă!")
                            elif e.response.status_code == 403:
                                st.warning("Contul tău nu a fost aprobat încă. Contactează un manager.")
                            else:
                                st.error(f"Eroare: {str(e)}")
                        except Exception as e:
                            st.error(f"Eroare: {str(e)}")

                if back:
                    main.empty()
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
                <div style="font-size: 1.9rem; font-weight: 700;">Înregistrare</div>
                <div style="font-size: 0.95rem; opacity: 0.78; margin-top: 0.3rem;">
                    Creează un cont nou în MedicSync
                </div>
            </div>
        """, unsafe_allow_html=True)

        role = st.selectbox(
            "Rol",
            options=["nurse", "doctor", "inventory_manager"],
            format_func=lambda x: {
                "nurse": "Asistent Medical",
                "doctor": "Doctor",
                "inventory_manager": "Manager Inventar"
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
                st.warning("Nu s-au putut încărca departamentele.")

        with st.form("register_form"):
            full_name = st.text_input("Nume Complet", placeholder="Dr. Ion Popescu")
            email = st.text_input("Email", placeholder="ion.popescu@spital.ro")
            password = st.text_input(
                "Parolă", type="password", placeholder="••••••••", help="Minim 6 caractere"
            )
            password_confirm = st.text_input("Confirmă Parola", type="password", placeholder="••••••••")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Înregistrare", use_container_width=True, type="primary")
            with col2:
                back = st.form_submit_button("Înapoi", use_container_width=True)

            if submit:
                if not all([full_name, email, password, password_confirm]):
                    st.error("Completează toate câmpurile!")
                elif password != password_confirm:
                    st.error("Parolele nu se potrivesc!")
                elif len(password) < 6:
                    st.error("Parola trebuie să aibă minim 6 caractere!")
                elif role in ("nurse", "doctor") and not dept_id:
                    st.error("Selectează o secție!")
                else:
                    try:
                        api_client = st.session_state.api_client
                        result = api_client.register(full_name, email, password, role, dept_id)
                        st.success(
                            f"Cont creat pentru **{result['full_name']}**! "
                            "Un manager va aproba accesul tău în scurt timp."
                        )
                        st.info("Revino la autentificare după ce primești confirmarea aprobării.")
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 409:
                            st.error("Email-ul este deja înregistrat!")
                        else:
                            st.error(f"Eroare la înregistrare: {str(e)}")
                    except Exception as e:
                        st.error(f"Eroare: {str(e)}")

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
                    <div style="margin-bottom: 1rem;"><svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#6c757d" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
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
