"""Stripe webhook handler — processes payment events from Stripe."""

from datetime import date, datetime, timezone
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session
from app.models.donation import Donation
from app.services.stripe_service import construct_webhook_event

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (payment_intent.succeeded, etc.)."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = construct_webhook_event(payload, sig_header)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {str(e)}")

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        payment_intent_id = intent["id"]

        async with async_session() as db:
            # Find the donation linked to this PaymentIntent
            result = await db.execute(
                select(Donation).where(Donation.stripe_payment_intent_id == payment_intent_id)
            )
            donation = result.scalar_one_or_none()

            if donation:
                donation.status = "completed"
                # Get receipt URL if available
                if intent.get("charges", {}).get("data"):
                    donation.receipt_url = intent["charges"]["data"][0].get("receipt_url")
                db.add(donation)
                await db.commit()

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        payment_intent_id = intent["id"]

        async with async_session() as db:
            result = await db.execute(
                select(Donation).where(Donation.stripe_payment_intent_id == payment_intent_id)
            )
            donation = result.scalar_one_or_none()

            if donation:
                donation.status = "failed"
                db.add(donation)
                await db.commit()

    elif event["type"] == "charge.refunded":
        charge = event["data"]["object"]
        payment_intent_id = charge.get("payment_intent")

        if payment_intent_id:
            async with async_session() as db:
                result = await db.execute(
                    select(Donation).where(Donation.stripe_payment_intent_id == payment_intent_id)
                )
                donation = result.scalar_one_or_none()

                if donation:
                    donation.status = "refunded"
                    db.add(donation)
                    await db.commit()

    return {"status": "ok"}
