"""Payment Methods router — card management for giving."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import get_db, Base
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])


# ── Model ─────────────────────────────────────────────────────────
class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), default="card")  # card, paypal, bank
    card_brand = Column(String(30), nullable=True)
    last_four = Column(String(4), nullable=True)
    exp_month = Column(Integer, nullable=True)
    exp_year = Column(Integer, nullable=True)
    cardholder_name = Column(String(200), nullable=True)
    is_default = Column(Boolean, default=False)
    billing_address = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


# ── Schemas ───────────────────────────────────────────────────────
class BillingAddress(BaseModel):
    full_name: Optional[str] = None
    country: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None


class PaymentMethodCreate(BaseModel):
    card_number: str
    exp_month: int
    exp_year: int
    cvv: str
    cardholder_name: Optional[str] = None
    billing_address: Optional[BillingAddress] = None


class PaymentMethodResponse(BaseModel):
    id: int
    type: str
    card_brand: Optional[str] = None
    last_four: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    cardholder_name: Optional[str] = None
    is_default: bool = False
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


def _detect_card_brand(number: str) -> str:
    if number.startswith("4"):
        return "visa"
    elif number.startswith(("51", "52", "53", "54", "55")):
        return "mastercard"
    elif number.startswith(("34", "37")):
        return "amex"
    elif number.startswith("6011"):
        return "discover"
    return "unknown"


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("")
async def list_payment_methods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    methods = (await db.execute(
        select(PaymentMethod).where(PaymentMethod.user_id == current_user.id)
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
    )).scalars().all()

    items = [{
        "id": m.id, "type": m.type, "card_brand": m.card_brand,
        "last_four": m.last_four, "exp_month": m.exp_month,
        "exp_year": m.exp_year, "cardholder_name": m.cardholder_name,
        "is_default": m.is_default,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in methods]
    return {"data": items}


@router.post("", status_code=201)
async def add_payment_method(
    data: PaymentMethodCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new payment method. Never stores raw card number."""
    clean_number = data.card_number.replace(" ", "").replace("-", "")
    brand = _detect_card_brand(clean_number)
    last_four = clean_number[-4:]

    # If first card, make it default
    existing_count = (await db.execute(
        select(PaymentMethod).where(PaymentMethod.user_id == current_user.id)
    )).scalars().all()
    is_default = len(existing_count) == 0

    pm = PaymentMethod(
        user_id=current_user.id,
        type="card",
        card_brand=brand,
        last_four=last_four,
        exp_month=data.exp_month,
        exp_year=data.exp_year,
        cardholder_name=data.cardholder_name,
        is_default=is_default,
        billing_address=data.billing_address.model_dump() if data.billing_address else None,
    )
    db.add(pm)
    await db.commit()
    await db.refresh(pm)

    return {"data": {
        "id": pm.id, "type": pm.type, "card_brand": pm.card_brand,
        "last_four": pm.last_four, "exp_month": pm.exp_month,
        "exp_year": pm.exp_year, "cardholder_name": pm.cardholder_name,
        "is_default": pm.is_default,
        "created_at": pm.created_at.isoformat() if pm.created_at else None,
    }}


@router.put("/{pm_id}/default")
async def set_default(
    pm_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Unset all defaults
    all_methods = (await db.execute(
        select(PaymentMethod).where(PaymentMethod.user_id == current_user.id)
    )).scalars().all()
    for m in all_methods:
        m.is_default = (m.id == pm_id)
        db.add(m)
    await db.commit()
    return {"data": {"id": pm_id, "is_default": True}}


@router.delete("/{pm_id}", status_code=204)
async def delete_payment_method(
    pm_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pm = (await db.execute(select(PaymentMethod).where(
        PaymentMethod.id == pm_id, PaymentMethod.user_id == current_user.id
    ))).scalar_one_or_none()
    if not pm:
        raise HTTPException(status_code=404, detail="Payment method not found")
    await db.delete(pm)
