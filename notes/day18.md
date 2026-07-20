# Day 18 — Load + secrets + backup + acceptance

## Locust baseline
- 30 concurrent: X req/sec, p95=Yms, Z% failures
- 50 concurrent: X req/sec, p95=Yms, Z% failures
- Breaking point: ~N concurrent (limited by Groq API latency, not code)

## Fixes
- notifications.py: sync Resend call wrapped in asyncio.to_thread (unblocked event loop)

## Secrets rotated
- Groq API key (old revoked)
- Resend API key (old revoked)
- Admin API key (old rows deactivated on cloud)

## Backup drill
- Cloud pg_dump succeeded, N MB
- Restored to local restore_test DB, all 9 tables + row counts match
- Restore time: ~X seconds

## SSL
- Cert issuer: [real CA]
- Expires: [date, 60+ days out]

## User acceptance
- N users tested
- M launch-blockers found and closed
- K cosmetic issues filed to v2-backlog

## Release candidate
- v1.0.0-rc2 tagged, ready for Day 19 soft launch