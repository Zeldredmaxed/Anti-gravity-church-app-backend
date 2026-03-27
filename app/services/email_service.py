"""Lightweight SMTP email service for sending song download links."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def send_song_download_email(
    to_email: str,
    song_title: str,
    artist_name: str,
    download_url: str,
    amount: float,
) -> bool:
    """Send the download link to a donor after a successful donation.

    Returns True if sent successfully, False otherwise.
    If SMTP is not configured, silently skips (returns False).
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print("[Email] SMTP not configured, skipping email send.")
        return False

    subject = f"🎵 Your song download — {song_title} by {artist_name}"

    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 520px; margin: auto; padding: 32px; background: #1a1a2e; color: #eee; border-radius: 16px;">
        <h1 style="color: #d4a574; margin-bottom: 4px;">Thank You for Your Gift! 🙏</h1>
        <p style="color: #aaa; font-size: 14px;">Your ${amount:.2f} donation blesses {artist_name}.</p>
        <div style="background: #16213e; border-radius: 12px; padding: 20px; margin: 24px 0; text-align: center;">
            <p style="font-size: 18px; font-weight: 600; color: #fff; margin: 0 0 4px 0;">{song_title}</p>
            <p style="color: #d4a574; margin: 0 0 16px 0;">by {artist_name}</p>
            <a href="{download_url}"
               style="display: inline-block; background: #d4a574; color: #1a1a2e; padding: 12px 32px;
                      border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 16px;">
                Download Your Song
            </a>
        </div>
        <p style="color: #666; font-size: 12px; text-align: center;">
            ChurchConnect &mdash; Where Faith Meets Music
        </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            if settings.SMTP_PORT != 25:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[Email] Song download sent to {to_email}")
        return True
    except Exception as e:
        print(f"[Email] Failed to send to {to_email}: {e}")
        return False
