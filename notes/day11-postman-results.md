# Day 11 Postman results

Session: day11-grok-run1
Provider: Grok (grok-4-fast)
Prompt version: v0.1

## Passed
- Turn 1-3: progressive slot filling
- Turn 4: full itinerary + search_campervans called
- Turn 9: save_lead + leads row created with normalized phone

## Deferred to Day 12
- (fill in any turns that produced weak replies)
- (fill in any missing itinerary sections)

## Test counts
- pytest -v: X passing, Y skipped
- Postman: X/10 turns behaving as expected
- DB: 10 user msgs, 10 assistant msgs, N tool_calls rows, 1 lead