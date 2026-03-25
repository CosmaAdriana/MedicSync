"""
MedicSync Frontend - Authentication & Authorization
Gestionează autentificarea utilizatorilor și session state.
"""
import streamlit as st
from api_client import APIClient


def init_session_state():
    """Initialize session state variables for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()


def login_page():
    """Display login form and handle authentication."""
    placeholder = st.empty()

    with placeholder.container():
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.title("🏥 MedicSync")
            st.subheader("Health 4.0 Platform")
            st.markdown("---")

            with st.form("login_form", clear_on_submit=False):
                st.markdown("### 🔐 Autentificare")

                email = st.text_input(
                    "Email",
                    placeholder="medic@spital.ro",
                )

                password = st.text_input(
                    "Parolă",
                    type="password",
                    placeholder="••••••••",
                )

                st.markdown("")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit = st.form_submit_button(
                        "🚀 Conectare",
                        use_container_width=True,
                        type="primary"
                    )
                with col_btn2:
                    register_btn = st.form_submit_button(
                        "📝 Înregistrare",
                        use_container_width=True
                    )

                if submit:
                    if not email or not password:
                        st.error("⚠️ Completează email și parola!")
                    else:
                        try:
                            api_client = st.session_state.api_client
                            api_client.login(email, password)
                            user = api_client.get_current_user()

                            st.session_state.authenticated = True
                            st.session_state.user = user

                            placeholder.empty()
                            st.rerun()

                        except requests.exceptions.HTTPError as e:
                            if e.response.status_code == 401:
                                st.error("❌ Email sau parolă incorectă!")
                            else:
                                st.error(f"❌ Eroare: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Eroare: {str(e)}")

                if register_btn:
                    st.session_state.show_register = True
                    st.rerun()

            st.markdown("---")
            st.caption("🏥 MedicSync © 2026 - Health 4.0 Platform")


def register_page():
    """Display registration form."""
    st.markdown("### 📝 Înregistrare Utilizator Nou")

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

    # Department selection for nurse/doctor — shown dynamically outside the form
    dept_id = None
    if role in ("nurse", "doctor"):
        try:
            api_client = st.session_state.api_client
            departments = api_client.get_departments()
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
        full_name = st.text_input(
            "Nume Complet",
            placeholder="Dr. Ion Popescu"
        )

        email = st.text_input(
            "Email",
            placeholder="ion.popescu@spital.ro"
        )

        password = st.text_input(
            "Parolă",
            type="password",
            placeholder="••••••••",
            help="Minim 6 caractere"
        )

        password_confirm = st.text_input(
            "Confirmă Parola",
            type="password",
            placeholder="••••••••"
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button(
                "✅ Înregistrare",
                use_container_width=True,
                type="primary"
            )
        with col2:
            back = st.form_submit_button(
                "◀️ Înapoi la Login",
                use_container_width=True
            )

        if submit:
            # Validation
            if not all([full_name, email, password, password_confirm]):
                st.error("⚠️ Te rugăm să completezi toate câmpurile!")
            elif password != password_confirm:
                st.error("❌ Parolele nu se potrivesc!")
            elif len(password) < 6:
                st.error("❌ Parola trebuie să aibă minim 6 caractere!")
            elif role in ("nurse", "doctor") and not dept_id:
                st.error("⚠️ Asistentii medicali și doctorii trebuie să selecteze o secție!")
            else:
                try:
                    api_client = st.session_state.api_client
                    result = api_client.register(full_name, email, password, role, dept_id)

                    st.success(f"✅ Cont creat cu succes pentru {result['full_name']}!")
                    st.info("👉 Acum te poți autentifica cu credențialele tale.")

                    # Auto-login
                    api_client.login(email, password)
                    user = api_client.get_current_user()
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.show_register = False

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
            st.session_state.show_register = False
            st.rerun()


def logout():
    """Clear session and logout user."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.api_client.clear_token()
    st.session_state.api_client = APIClient()
    st.rerun()


def require_auth(allowed_roles: list = None):
    """
    Require authentication for a page. Call at the top of each protected page.

    Args:
        allowed_roles: List of allowed roles (e.g., ["manager", "doctor"])
                      If None, any authenticated user can access.

    Example:
        require_auth(allowed_roles=["manager", "doctor"])
    """
    init_session_state()
    if not st.session_state.authenticated:
        st.warning("⚠️ Trebuie să te autentifici pentru a accesa această pagină.")
        st.info("👈 Folosește formularul de login din sidebar sau pagina principală.")
        st.stop()

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


# Import requests for error handling
import requests
