"""
MedicSync Frontend - API Client
Wrapper pentru requests către backend FastAPI.
"""
import requests
from typing import Optional, Dict, Any
from config import API_BASE_URL


class APIClient:
    """Client pentru comunicarea cu backend-ul MedicSync."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None

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
        """
        GET request wrapper.

        Args:
            endpoint: API endpoint (e.g., "/departments/")
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict) -> Any:
        """
        POST request wrapper.

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            JSON response data
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=self._headers(), json=data)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: Dict) -> Any:
        """PUT request wrapper."""
        url = f"{self.base_url}{endpoint}"
        response = requests.put(url, headers=self._headers(), json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint: str) -> Any:
        """DELETE request wrapper."""
        url = f"{self.base_url}{endpoint}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
        return response.json() if response.content else None

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
        response = requests.patch(url, headers=self._headers(), json={"status": new_status})
        response.raise_for_status()
        return response.json()

    def resolve_alert(self, patient_id: int, alert_id: int) -> Dict:
        """Mark a clinical alert as resolved."""
        url = f"{self.base_url}/patients/{patient_id}/alerts/{alert_id}/resolve"
        response = requests.patch(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

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
                             department_id: int = None) -> Dict:
        """Create new inventory item."""
        data = {
            "product_name": product_name,
            "current_stock": current_stock,
            "min_stock_level": min_stock_level,
            "expiration_date": expiration_date,
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
        return self.put(f"/orders/{order_id}/status", {"new_status": new_status})

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
