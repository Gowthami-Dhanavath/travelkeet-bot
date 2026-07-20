# Day 18 Locust baseline

At 30 concurrent: 7.4 req/sec, p95=1900ms, failures=86%
At 50 concurrent: 7.4 req/sec, p95=2400ms, failures=85%
Breaking point: ~30-50 concurrent
Primary bottleneck: high request failure rate under concurrent load (investigate failure responses / external API limits)