# Day 14 — Live data + lead capture end to end

## Deliverable met
A full staging conversation produces a real lead row plus a sales
notification email, using live campervan data.

## What's live on Railway
- POST /admin/data/sync (manual trigger for campervan upsert)
- GET /admin/leads (list + filter by status)
- PATCH /admin/leads/{id} (status transitions, notes, assignment)
- Lead capture in save_lead tool fires Resend email to sales

## Env vars added on Railway
- RESEND_API_KEY (real)
- SALES_NOTIFICATION_EMAIL (temporary: my own email; swap for sales inbox pre-launch)
- ADMIN_API_KEY_HASH (real, cloud-persisted admin key)

## Deferred to later
- Domain verification for Resend (currently sending from onboarding@resend.dev sandbox)
- Real SYNC_FEED_URL (site team hasn't provided feed URL; using seed snapshot)
- Railway cron (best-effort; falls back to manual sync trigger)

## Testing evidence
- Cloud conversation day14-cloud-001 produced Priya Sharma lead
- Email received at my address with correct trip summary
- /admin/leads returns the lead
- /admin/data/sync returns {"upserted": 10, "deactivated": 0}