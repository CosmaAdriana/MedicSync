"""
MedicSync — ORM Models
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


# ========================== Enums ==========================================

class RoleEnum(str, enum.Enum):
    """User roles within the hospital system."""
    doctor = "doctor"
    nurse = "nurse"
    manager = "manager"
    inventory_manager = "inventory_manager"



class PatientStatusEnum(str, enum.Enum):
    """Current status of a patient."""
    admitted = "admitted"
    discharged = "discharged"
    critical = "critical"


class RiskLevelEnum(str, enum.Enum):
    """Clinical alert severity levels."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class OrderStatusEnum(str, enum.Enum):
    """Lifecycle of a supply order matching the UML State Machine Diagram."""
    draft = "draft"
    placed = "placed"
    processed = "processed"
    rejected = "rejected"
    delivered = "delivered"

# ========================== Models =========================================

class Department(Base):
    """
    Hospital department/section (e.g., UPU, Cardiologie, Pediatrie).
    Used for organizing staff, patients, and predicting resource needs per section.
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Relationships
    patients = relationship("Patient", back_populates="department")
    shifts = relationship("Shift", back_populates="department")
    patient_flows = relationship("DailyPatientFlow", back_populates="department")

    def __repr__(self) -> str:
        return f"<Department {self.name}>"


class User(Base):
    """
    Hospital staff member (doctor, nurse, or admin).
    Passwords are stored as bcrypt hashes.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.nurse)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    # Relationships
    shifts = relationship("Shift", back_populates="user")
    department = relationship("Department", foreign_keys=[department_id])

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"


class Patient(Base):
    """
    A patient admitted to the hospital ward.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    admission_date = Column(Date, nullable=False, default=date.today)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    status = Column(
        Enum(PatientStatusEnum),
        nullable=False,
        default=PatientStatusEnum.admitted,
    )

    # Relationships
    department = relationship("Department", back_populates="patients")
    vital_signs = relationship("VitalSign", back_populates="patient")
    clinical_alerts = relationship("ClinicalAlert", back_populates="patient")

    def __repr__(self) -> str:
        return f"<Patient {self.full_name} ({self.status.value})>"


class VitalSign(Base):
    """
    Vital signs recorded at the patient's bedside.
    Each record is a snapshot in time of the patient's clinical state.
    """
    __tablename__ = "vital_signs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    blood_pressure = Column(String(20), nullable=False)        # e.g. "120/80"
    pulse = Column(Integer, nullable=False)                     # bpm
    respiratory_rate = Column(Integer, nullable=False)          # breaths/min
    oxygen_saturation = Column(Float, nullable=False)           # SpO2 %
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="vital_signs")

    def __repr__(self) -> str:
        return f"<VitalSign patient={self.patient_id} @ {self.recorded_at}>"


class ClinicalAlert(Base):
    """
    Automated clinical alert generated when vital signs indicate risk.
    Links to the patient whose condition triggered it.
    """
    __tablename__ = "clinical_alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    risk_level = Column(Enum(RiskLevelEnum), nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="clinical_alerts")

    def __repr__(self) -> str:
        return f"<ClinicalAlert patient={self.patient_id} level={self.risk_level.value}>"

class Order(Base):
    """
    Supply order managed by the logistic admin.
    Starts as 'draft', moves to 'placed', 'processed', and 'delivered'.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.draft)
    total_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    items = relationship("OrderItem", back_populates="order")
    admin = relationship("User")

    def __repr__(self) -> str:
        return f"<Order #{self.id} status={self.status.value}>"


class OrderItem(Base):
    """
    Association table (N:M) detailing the quantity of each inventory item in an order.
    Matches the loop fragment in the UML Sequence Diagram.
    """
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    item = relationship("InventoryItem")

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id} item={self.inventory_item_id} qty={self.quantity}>"


class InventoryItem(Base):
    """
    Medical supply tracked under FEFO policy.
    ExpirationDate is required for First-Expired-First-Out logic.
    """
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    min_stock_level = Column(Integer, nullable=False, default=0)
    expiration_date = Column(Date, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    department = relationship("Department", foreign_keys=[department_id])

    def __repr__(self) -> str:
        return f"<InventoryItem {self.product_name} qty={self.current_stock}>"


class Shift(Base):
    """
    Work shift assigned to a staff member.
    Used for staff scheduling optimization.
    """
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="shifts")
    department = relationship("Department", back_populates="shifts")

    def __repr__(self) -> str:
        return f"<Shift user={self.user_id} {self.start_time} → {self.end_time}>"


class DailyPatientFlow(Base):
    """
    Historical daily patient admission data with exogenous variables
    for ML prediction. Per-department granularity.
    """
    __tablename__ = "daily_patient_flow"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    patient_count = Column(Integer, nullable=False)
    weather_temp = Column(Float, nullable=True)         # °C — exogenous variable
    is_holiday = Column(Boolean, nullable=False, default=False)
    is_epidemic = Column(Boolean, nullable=False, default=False)

    # Relationships
    department = relationship("Department", back_populates="patient_flows")

    def __repr__(self) -> str:
        return f"<DailyPatientFlow {self.date} count={self.patient_count}>"
