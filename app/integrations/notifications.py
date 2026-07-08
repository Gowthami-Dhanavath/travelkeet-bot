"""Sales team notifications via Resend."""
import logging
from typing import Any

import resend

from app.config import settings
from app.db.models import Lead

logger = logging.getLogger(__name__)


async def send_lead_notification(
    lead: Lead,
    transcript_url: str | None = None,
) -> dict[str, Any]:
    """Email the sales team about a new lead.

    Never raises. Failures log and return {"ok": False, "error": ...}
    because a Resend outage should not fail the /v1/chat request.
    """
    if not settings.resend_api_key:
        logger.warning("send_lead_notification skipped: RESEND_API_KEY not set")
        return {"ok": False, "error": "not_configured"}

    if not settings.sales_notification_email:
        logger.warning("send_lead_notification skipped: SALES_NOTIFICATION_EMAIL not set")
        return {"ok": False, "error": "not_configured"}

    resend.api_key = settings.resend_api_key

    ts = lead.trip_summary or {}
    van_line = (
        f"<p><strong>Recommended van:</strong> {lead.recommended_van_id}</p>"
        if lead.recommended_van_id else ""
    )
    transcript_line = (
        f'<p><a href="{transcript_url}">View chat transcript</a></p>'
        if transcript_url else ""
    )
    email_line = f"<li><strong>Email:</strong> {lead.email}</li>" if lead.email else ""

    html = f"""
    <h2 style="color:#0f172a">New TravelKeet AI lead</h2>
    <p style="font-size:16px"><strong>{lead.name}</strong> &mdash; {lead.phone}</p>
    <h3>Trip details</h3>
    <ul>
      {email_line}
      <li><strong>Route:</strong> {lead.pickup_city or '?'} to {lead.destination_city or '?'}</li>
      <li><strong>Dates:</strong> {ts.get('travel_dates', '?')}</li>
      <li><strong>People:</strong> {lead.num_people or '?'}</li>
      <li><strong>Budget:</strong> INR {lead.budget_inr or '?'}</li>
      <li><strong>Food preference:</strong> {ts.get('food_preference', '?')}</li>
    </ul>
    {van_line}
    {transcript_line}
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0">
    <p style="color:#94a3b8;font-size:12px">Lead ID: {lead.id}</p>
    """

    subject = (
        f"New AI lead — {lead.name} "
        f"({lead.pickup_city or 'unknown'} to {lead.destination_city or 'unknown'})"
    )

    try:
        response = resend.Emails.send({
            "from": "TravelKeet AI <onboarding@resend.dev>",
            "to": [settings.sales_notification_email],
            "subject": subject,
            "html": html,
        })
        logger.info(
            "Lead email sent",
            extra={"lead_id": str(lead.id), "resend_id": response.get("id")},
        )
        return {"ok": True, "resend_id": response.get("id")}
    except Exception as e:
        logger.exception("Lead email failed")
        return {"ok": False, "error": str(e)}