"""
MedicSync - Cache Layer
TTL-uri mari + invalidare explicită după mutații (via .clear()).
Cache-ul e keyed pe token → utilizatori diferiți primesc date diferite.
"""
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import streamlit as st


def _client(token: str):
    from api_client import APIClient
    from config import API_BASE_URL
    c = APIClient(API_BASE_URL)
    c.set_token(token)
    return c


@st.cache_data(ttl=None, show_spinner=False)
def get_departments(token: str) -> list:
    return _client(token).get_departments()


@st.cache_data(ttl=None, show_spinner=False)
def get_hospital_stats(token: str) -> list:
    return _client(token).get_hospital_stats()


@st.cache_data(ttl=None, show_spinner=False)
def get_patients(token: str, status: Optional[str] = None) -> list:
    return _client(token).get_patients(status=status)


@st.cache_data(ttl=None, show_spinner=False)
def get_inventory(token: str) -> list:
    return _client(token).get_inventory()


@st.cache_data(ttl=None, show_spinner=False)
def get_fefo_alerts(token: str) -> list:
    return _client(token).get_fefo_alerts()


@st.cache_data(ttl=None, show_spinner=False)
def get_orders(token: str) -> list:
    return _client(token).get_orders()


@st.cache_data(ttl=None, show_spinner=False)
def get_patient_vitals(token: str, patient_id: int) -> list:
    return _client(token).get_patient_vitals(patient_id)


@st.cache_data(ttl=60, show_spinner=False)
def get_patient_alerts(token: str, patient_id: int) -> list:
    return _client(token).get_patient_alerts(patient_id)


@st.cache_data(ttl=None, show_spinner=False)
def get_consumption_stats(token: str) -> list:
    return _client(token).get_consumption_stats()


@st.cache_data(ttl=None, show_spinner=False)
def get_vacation_balance(token: str, year: int) -> dict:
    return _client(token).get_vacation_balance(year=year)


@st.cache_data(ttl=None, show_spinner=False)
def get_vacation_requests(token: str, department_id: int = None) -> list:
    return _client(token).get_vacation_requests(department_id=department_id)


@st.cache_data(ttl=None, show_spinner=False)
def get_monthly_schedule(token: str, dept_id: int, year: int, month: int) -> dict:
    return _client(token).get_monthly_schedule(dept_id, year, month)


@st.cache_data(ttl=30, show_spinner=False)
def get_notifications_summary(token: str) -> dict:
    return _client(token).get_notifications_summary()


def fetch_parallel(**calls) -> dict:
    """
    Apelează mai multe funcții cache în paralel.
    Sintaxă: fetch_parallel(key=(fn, arg1, arg2), ...)
    Returnează: {key: result}
    """
    with ThreadPoolExecutor() as ex:
        futures = {name: ex.submit(fn, *args) for name, (fn, *args) in calls.items()}
        return {name: future.result() for name, future in futures.items()}


def prefetch_all_async(token: str):
    """
    Pornește un thread în background care încălzește cache-ul pentru toate
    endpoint-urile comune. Apelat o singură dată după login.
    """
    import threading

    def _warm():
        try:
            with ThreadPoolExecutor(max_workers=8) as ex:
                ex.submit(get_departments,    token)
                ex.submit(get_hospital_stats, token)
                ex.submit(get_patients,       token)
                ex.submit(get_patients,       token, "admitted")
                ex.submit(get_patients,       token, "critical")
                ex.submit(get_inventory,         token)
                ex.submit(get_fefo_alerts,       token)
                ex.submit(get_orders,            token)
                ex.submit(get_consumption_stats, token)
        except Exception:
            pass  # prefetch silențios — nu blochează UI-ul

    threading.Thread(target=_warm, daemon=True).start()
