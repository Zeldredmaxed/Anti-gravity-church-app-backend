"""Notification service — SMS (Twilio), Email (SendGrid), and Push (placeholder)."""

from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


# ── SMS via Twilio ──────────────────────────────────────────────────────────

async def send_sms(to: str, body: str) -> dict:
    """Send an SMS message via Twilio.

    Returns {"status": "sent", "sid": "..."} on success.
    Returns {"status": "skipped", "reason": "..."} if not configured.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio not configured — SMS skipped")
        return {"status": "skipped", "reason": "Twilio credentials not configured"}

    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=body,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to,
    )
    logger.info(f"SMS sent to {to}: SID={message.sid}")
    return {"status": "sent", "sid": message.sid}


# ── Email via SendGrid ──────────────────────────────────────────────────────

async def send_email(
    to: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
) -> dict:
    """Send an email via SendGrid.

    Returns {"status": "sent", "status_code": 202} on success.
    Returns {"status": "skipped", "reason": "..."} if not configured.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured — email skipped")
        return {"status": "skipped", "reason": "SendGrid API key not configured"}

    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content

    sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    sender = from_email or settings.SENDGRID_FROM_EMAIL or settings.SMTP_FROM_EMAIL
    
    mail = Mail(
        from_email=Email(sender),
        to_emails=To(to),
        subject=subject,
        html_content=Content("text/html", html_body),
    )

    response = sg.client.mail.send.post(request_body=mail.get())
    logger.info(f"Email sent to {to}: status_code={response.status_code}")
    return {"status": "sent", "status_code": response.status_code}


# ── Push Notification (Firebase placeholder) ─────────────────────────────────

async def send_push(user_id: int, title: str, body: str) -> dict:
    """Send a push notification. Placeholder for Firebase Cloud Messaging.

    When ready, add FIREBASE_CREDENTIALS to config and implement here.
    """
    logger.info(f"Push notification placeholder: user={user_id}, title={title}")
    return {"status": "placeholder", "message": "Push notifications not yet configured"}


# ── Convenience helper ───────────────────────────────────────────────────────

async def send_notification(
    channel: str,
    to: str,
    subject: Optional[str] = None,
    body: str = "",
    user_id: Optional[int] = None,
) -> dict:
    """Unified notification dispatcher.

    Args:
        channel: "sms", "email", or "push"
        to: Phone number (SMS) or email address (Email)
        subject: Email subject (only for email)
        body: Message body or HTML
        user_id: User ID (only for push)
    """
    if channel == "sms":
        return await send_sms(to=to, body=body)
    elif channel == "email":
        return await send_email(to=to, subject=subject or "Notification", html_body=body)
    elif channel == "push":
        return await send_push(user_id=user_id or 0, title=subject or "Notification", body=body)
    else:
        return {"status": "error", "reason": f"Unknown channel: {channel}"}
