# Day 15 — Resilience + observability

## Delivered
- Retry + circuit breaker on Groq calls (system degrades gracefully on failure)
- Slot extraction on llama-3.1-8b-instant → ~10x cheaper per turn
- /v1/health checks DB + Groq + Resend
- /admin/metrics: cost, conversation count, latency percentiles, lead conversion
- Daily cost alert cron (yesterday's spend > $5 → email ops)

## Deferred to later
- Prompt caching optimization (Groq auto-caches stable prefixes; no API knobs today)
- Cost tracking in orchestrator: verify Person A's handle_message calls
  conv_repo.update_usage with real token counts; currently may be 0

## Testing evidence
- Health endpoint returns status:ok with all 3 checks green
- Metrics endpoint returns non-zero cost, conv count, latency percentiles
- Cost alert script runs standalone (below threshold, no email fired)