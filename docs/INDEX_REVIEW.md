# Index Review — Day 9

## Goal
Verify that all hot queries use indexes or are index-ready for production scale.

---

## 1. Campervan Search Query

### SQL tested
```sql
SELECT * FROM campervans
WHERE is_active = true
AND base_city = 'Mumbai'
AND capacity >= 4
ORDER BY price_per_day ASC
LIMIT 20;