"""Daily cost alert — emails ops if yesterday's spend exceeds threshold."""
import logging
from datetime import datetime, timedelta, timezone

import resend
from sqlalchemy import func, select

from app.config import settings
from app.db.models import Conversation
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

DAILY_THRESHOLD_CENTS = 500   # $5/day baseline — tune per plan constraints


async def check_and_alert() -> dict:
    """Sum yesterday's costs; alert if over threshold."""
    now = datetime.now(timezone.utc)
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = yesterday_start + timedelta(days=1)

    async with AsyncSessionLocal() as db:
        total_cents = (await db.execute(
            select(func.coalesce(func.sum(Conversation.cost_cents), 0))
            .where(Conversation.created_at >= yesterday_start)
            .where(Conversation.created_at < yesterday_end)
        )).scalar_one()

        conv_count = (await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.created_at >= yesterday_start)
            .where(Conversation.created_at < yesterday_end)
        )).scalar_one()

    logger.info(
        "Daily cost check",
        extra={
            "date": yesterday_start.date().isoformat(),
            "cost_cents": int(total_cents),
            "conversations": conv_count,
        },
    )

    if total_cents < DAILY_THRESHOLD_CENTS:
        return {"alerted": False, "cost_cents": int(total_cents), "conversations": conv_count}

    if not settings.resend_api_key or not settings.sales_notification_email:
        logger.warning("Cost over threshold but no email configured")
        return {"alerted": False, "reason": "no_email", "cost_cents": int(total_cents)}

    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send({
            "from": "TravelKeet Ops <onboarding@resend.dev>",
            "to": [settings.sales_notification_email],
            "subject": f"[ALERT] TravelKeet AI daily cost: ${int(total_cents)/100:.2f}",
            "html": f"""
            <h2>Daily cost alert</h2>
            <p>Yesterday ({yesterday_start.date()}):</p>
            <ul>
              <li>Total spend: <strong>${int(total_cents)/100:.2f}</strong></li>
              <li>Conversations: {conv_count}</li>
              <li>Cost per conversation: ${(int(total_cents)/max(conv_count,1))/100:.4f}</li>
              <li>Threshold: ${DAILY_THRESHOLD_CENTS/100:.2f}</li>
            </ul>
            <p>Review usage or increase threshold in app/workers/cost_alert.py.</p>
            """,
        })
    except Exception:
        logger.exception("Cost alert email failed")
        return {"alerted": False, "reason": "email_failed", "cost_cents": int(total_cents)}

    return {"alerted": True, "cost_cents": int(total_cents), "conversations": conv_count}


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(check_and_alert())
    print(f"Cost alert result: {result}")