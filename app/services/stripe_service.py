"""Stripe payment gateway service — handles PaymentIntents, customers, and webhooks."""

from typing import Optional
from app.config import settings


def _get_stripe():
    """Lazily import and configure stripe only when keys are present."""
    import stripe
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("STRIPE_SECRET_KEY not configured in environment")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


async def create_customer(email: str, name: str, member_id: int) -> str:
    """Create a Stripe Customer and return the customer ID."""
    stripe = _get_stripe()
    customer = stripe.Customer.create(
        email=email,
        name=name,
        metadata={"member_id": str(member_id)},
    )
    return customer.id


async def create_payment_intent(
    amount_cents: int,
    currency: str = "usd",
    customer_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Create a Stripe PaymentIntent. Returns {client_secret, payment_intent_id}."""
    stripe = _get_stripe()
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        customer=customer_id,
        description=description or "Church Donation",
        metadata=metadata or {},
        automatic_payment_methods={"enabled": True},
    )
    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
    }


async def confirm_payment(payment_intent_id: str) -> dict:
    """Retrieve a PaymentIntent to check its status."""
    stripe = _get_stripe()
    intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    return {
        "id": intent.id,
        "status": intent.status,
        "amount": intent.amount,
        "receipt_url": intent.charges.data[0].receipt_url if intent.charges.data else None,
    }


def construct_webhook_event(payload: bytes, sig_header: str) -> object:
    """Verify and construct a Stripe webhook event."""
    stripe = _get_stripe()
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured")
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
