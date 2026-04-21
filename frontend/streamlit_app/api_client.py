"""
MedicSync Frontend - API Client
Wrapper pentru requests către backend FastAPI.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any
from config import API_BASE_URL


class SessionExpiredException(Exception):
    """Ridicată când backend-ul returnează 401 — token JWT expirat."""
    pass


def _make_session() -> requests.Session:
    """Creează un requests.Session cu connection pooling și retry automat."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class APIClient:
    """Client pentru comunicarea cu backend-ul MedicSync."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self._session = _make_session()

    def _check(self, response: requests.Response) -> requests.Response:
        """Verifică răspunsul; ridică SessionExpiredException la 401 doar când utilizatorul era deja autentificat."""
        if response.status_code == 401 and self.token:
            raise SessionExpiredException("Sesiunea a expirat.")
        response.raise_for_status()
        return response

    def set_token(self, token: str):
        """Set JWT token for authenticated requests."""
        self.token = token

    def clear_token(self):
        """Clear authentication token."""
        self.token = None

    def _headers(self) -> Dict[str, str]:
        """Build request headers with auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        return self._check(self._session.get(url, headers=self._headers(), params=params)).json()

    def post(self, endpoint: str, data: Dict) -> Any:
        url = f"{self.base_url}{endpoint}"
        return self._check(self._session.post(url, headers=self._headers(), json=data)).json()

    def put(self, endpoint: str, data: Dict) -> Any:
        url = f"{self.base_url}{endpoint}"
        return self._check(self._session.put(url, headers=self._headers(), json=data)).json()

    def delete(self, endpoint: str) -> Any:
        url = f"{self.base_url}{endpoint}"
        r = self._check(self._session.delete(url, headers=self._headers()))
        return r.json() if r.content else None

    # ========== Authentication Methods ==========

    def login(self, email: str, password: str) -> Dict:
        """
        Authenticate user and store token.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with access_token and token_type
        """
        response = self.post("/auth/login", {"email": email, "password": password})
        self.set_token(response["access_token"])
        return response

    def register(self, full_name: str, email: str, password: str, role: str,
                 department_id: int = None) -> Dict:
        """Register new user."""
        data = {"full_name": full_name, "email": email, "password": password, "role": role}
        if department_id:
            data["department_id"] = department_id
        return self.post("/auth/register", data)

    def get_current_user(self) -> Dict:
        """Get current authenticated user details."""
        return self.get("/auth/me")

    # ========== Departments ==========

    def get_departments(self) -> list:
        """Get all departments."""
        return self.get("/departments/")

    def create_department(self, name: str, description: str = None) -> Dict:
        """Create new department (manager only)."""
        return self.post("/departments/", {"name": name, "description": description})

    # ========== Patients ==========

    def get_hospital_stats(self) -> list:
        """Get patient counts per department for the entire hospital."""
        return self.get("/patients/hospital-stats")

    def get_patients(self, status: str = None) -> list:
        """Get all patients, optionally filtered by status."""
        params = {"status": status} if status else None
        return self.get("/patients/", params=params)

    def get_patient(self, patient_id: int) -> Dict:
        """Get specific patient details."""
        return self.get(f"/patients/{patient_id}")

    def create_patient(self, full_name: str, department_id: int,
                      admission_date: str, status: str = "admitted") -> Dict:
        """Create new patient."""
        return self.post("/patients/", {
            "full_name": full_name,
            "department_id": department_id,
            "admission_date": admission_date,
            "status": status
        })

    def update_patient_status(self, patient_id: int, new_status: str) -> Dict:
        """Update patient status (doctor/manager only)."""
        url = f"{self.base_url}/patients/{patient_id}/status"
        return self._check(self._session.patch(url, headers=self._headers(), json={"status": new_status})).json()

    def resolve_alert(self, patient_id: int, alert_id: int) -> Dict:
        """Mark a clinical alert as resolved."""
        url = f"{self.base_url}/patients/{patient_id}/alerts/{alert_id}/resolve"
        return self._check(self._session.patch(url, headers=self._headers())).json()

    def get_patient_vitals(self, patient_id: int) -> list:
        """Get vital signs for a patient."""
        return self.get(f"/patients/{patient_id}/vitals")

    def get_patient_alerts(self, patient_id: int) -> list:
        """Get clinical alerts for a patient."""
        return self.get(f"/patients/{patient_id}/alerts")

    # ========== Vital Signs ==========

    def record_vitals(self, patient_id: int, blood_pressure: str, pulse: int,
                     respiratory_rate: int, oxygen_saturation: float) -> Dict:
        """Record new vital signs (nurse only)."""
        return self.post("/vitals/", {
            "patient_id": patient_id,
            "blood_pressure": blood_pressure,
            "pulse": pulse,
            "respiratory_rate": respiratory_rate,
            "oxygen_saturation": oxygen_saturation
        })

    # ========== Inventory ==========

    def get_inventory(self) -> list:
        """Get all inventory items."""
        return self.get("/inventory/")

    def get_fefo_alerts(self) -> list:
        """Get FEFO (First-Expired-First-Out) alerts."""
        return self.get("/inventory/fefo-alerts")

    def create_inventory_item(self, product_name: str, current_stock: int,
                             min_stock_level: int, expiration_date: str,
                             unit_price: float = 0.0,
                             department_id: int = None) -> Dict:
        """Create new inventory item."""
        data = {
            "product_name": product_name,
            "current_stock": current_stock,
            "min_stock_level": min_stock_level,
            "expiration_date": expiration_date,
            "unit_price": unit_price,
        }
        if department_id:
            data["department_id"] = department_id
        return self.post("/inventory/", data)

    def update_inventory_stock(self, item_id: int, current_stock: int,
                              expiration_date: str = None) -> Dict:
        """Update inventory stock levels."""
        data = {"current_stock": current_stock}
        if expiration_date:
            data["expiration_date"] = expiration_date
        return self.put(f"/inventory/{item_id}", data)

    # ========== Predictions (ML) ==========

    def predict_staff_needs(self, date: str, department_id: int, weather_temp: float,
                           is_holiday: bool = False, is_epidemic: bool = False) -> Dict:
        """
        Get ML prediction for staff needs.

        Args:
            date: Target date (YYYY-MM-DD)
            department_id: Department ID
            weather_temp: Temperature in Celsius
            is_holiday: Is it a holiday?
            is_epidemic: Is there an epidemic?

        Returns:
            Prediction with patient count and recommended nurses
        """
        return self.get("/predict/staff-needs", params={
            "date": date,
            "department_id": department_id,
            "weather_temp": weather_temp,
            "is_holiday": is_holiday,
            "is_epidemic": is_epidemic
        })

    def get_model_info(self) -> Dict:
        """Get real ML model metrics and feature importances."""
        return self.get("/predict/model-info")

    def predict_inventory_safety_stock(self, lead_time_std: float = 2.0) -> list:
        """Get safety stock predictions for inventory."""
        return self.get("/predict/inventory", params={"lead_time_std": lead_time_std})

    # ========== Orders ==========

    def get_orders(self) -> list:
        """Get all orders."""
        return self.get("/orders/")

    def create_order(self, items: list) -> Dict:
        """
        Create new order.

        Args:
            items: List of dicts with inventory_item_id, quantity, unit_price
        """
        return self.post("/orders/", {"items": items})

    def update_order_status(self, order_id: int, new_status: str) -> Dict:
        """Update order status."""
        url = f"{self.base_url}/orders/{order_id}/status"
        return self._check(self._session.put(url, headers=self._headers(), params={"new_status": new_status})).json()

    # ========== Shifts ==========

    def get_shifts(self) -> list:
        """Get all shifts."""
        return self.get("/shifts/")

    def create_shift(self, user_id: int, department_id: int,
                    start_time: str, end_time: str) -> Dict:
        """Create new shift (manager only)."""
        return self.post("/shifts/", {
            "user_id": user_id,
            "department_id": department_id,
            "start_time": start_time,
            "end_time": end_time
        })

    # ========== Schedule / Grafic ==========

    def get_vacation_balance(self, year: int = None) -> Dict:
        params = {"year": year} if year else {}
        return self.get("/schedule/balance", params=params)

    def get_vacation_requests(self, department_id: int = None, month: int = None, year: int = None) -> list:
        params = {}
        if department_id: params["department_id"] = department_id
        if month: params["month"] = month
        if year: params["year"] = year
        return self.get("/schedule/requests", params=params)

    def create_vacation_request(self, request_type: str, start_date: str,
                                 end_date: str, notes: str = None) -> Dict:
        data = {"request_type": request_type, "start_date": start_date, "end_date": end_date}
        if notes:
            data["notes"] = notes
        return self.post("/schedule/requests", data)

    def review_vacation_request(self, request_id: int, status: str) -> Dict:
        url = f"{self.base_url}/schedule/requests/{request_id}"
        return self._check(
            self._session.patch(url, headers=self._headers(), json={"status": status})
        ).json()

    def generate_schedule(self, department_id: int, year: int, month: int) -> Dict:
        return self.post("/schedule/generate", {
            "department_id": department_id, "year": year, "month": month
        })

    def get_monthly_schedule(self, department_id: int, year: int, month: int) -> Dict:
        return self.get("/schedule/monthly", params={
            "department_id": department_id, "year": year, "month": month
        })

    def save_schedule(self, department_id: int, year: int, month: int,
                      schedule_data: str, is_finalized: bool = False) -> Dict:
        return self.post("/schedule/save", {
            "department_id": department_id,
            "year": year,
            "month": month,
            "schedule_data": schedule_data,
            "is_finalized": is_finalized,
        })
