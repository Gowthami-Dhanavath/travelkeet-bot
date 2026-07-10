"""Admin metrics endpoint — cost, throughput, latency, conversion."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.models import Conversation, Lead, Message, ToolCall
from app.db.session import get_db_session
from app.deps import AdminKey

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics")
async def metrics(
    key: AdminKey,
    days: int = Query(default=1, ge=1, le=30),
    db: AsyncSession = Depends(get_db_session),
):
    """Aggregate metrics for the last N days (default 1).

    Returns cost, conversation count, latency percentiles, and lead conversion.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Conversation count + token totals + cost
    conv_stats = (await db.execute(
        select(
            func.count(Conversation.id).label("count"),
            func.coalesce(func.sum(Conversation.total_tokens_in), 0).label("tokens_in"),
            func.coalesce(func.sum(Conversation.total_tokens_out), 0).label("tokens_out"),
            func.coalesce(func.sum(Conversation.cost_cents), 0).label("cost_cents"),
        ).where(Conversation.created_at >= since)
    )).one()

    # Message count for avg-turns
    msg_count = (await db.execute(
        select(func.count(Message.id)).where(
            Message.role == "user",
            Message.created_at >= since,
        )
    )).scalar_one()

    # Latency percentiles from messages (assistant only, where latency_ms recorded)
    lat_rows = (await db.execute(
        select(Message.latency_ms).where(
            Message.role == "assistant",
            Message.latency_ms.is_not(None),
            Message.created_at >= since,
        ).order_by(Message.latency_ms)
    )).scalars().all()

    def _pct(sorted_list, p):
        if not sorted_list:
            return None
        idx = min(int(len(sorted_list) * p), len(sorted_list) - 1)
        return sorted_list[idx]

    # Tool calls
    tool_stats = (await db.execute(
        select(
            ToolCall.tool_name,
            func.count(ToolCall.id).label("count"),
            func.coalesce(
                func.sum(cast(ToolCall.success, Integer)),
                0,
            ).label("n_success"),
        )
        .where(ToolCall.created_at >= since)
        .group_by(ToolCall.tool_name)
    )).all()

    # Lead conversion
    lead_count = (await db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= since)
    )).scalar_one()

    lead_by_status = (await db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(Lead.created_at >= since)
        .group_by(Lead.status)
    )).all()

    total_convs = conv_stats.count or 0
    return {
        "since": since.isoformat(),
        "days": days,
        "conversations": {
            "count": total_convs,
            "user_messages": msg_count,
            "avg_turns": round(msg_count / total_convs, 1) if total_convs else 0,
        },
        "cost": {
            "tokens_in": int(conv_stats.tokens_in),
            "tokens_out": int(conv_stats.tokens_out),
            "cost_cents": int(conv_stats.cost_cents),
            "cost_inr": round(int(conv_stats.cost_cents) / 100 * 84, 2),  # rough INR conversion
            "cost_per_conversation_cents": (
                round(int(conv_stats.cost_cents) / total_convs, 2) if total_convs else 0
            ),
        },
        "latency_ms": {
            "p50": _pct(lat_rows, 0.50),
            "p95": _pct(lat_rows, 0.95),
            "p99": _pct(lat_rows, 0.99),
            "sample_size": len(lat_rows),
        },
        "tools": [
            {"name": t.tool_name, "calls": t.count, "success": t.n_success}
            for t in tool_stats
        ],
        "leads": {
            "count": lead_count,
            "conversion_rate": round(lead_count / total_convs, 3) if total_convs else 0,
            "by_status": {row[0]: row[1] for row in lead_by_status},
        },
    }