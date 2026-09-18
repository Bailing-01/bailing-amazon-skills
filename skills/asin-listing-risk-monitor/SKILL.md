---
name: ASIN Listing 风险监控
description: use this when checking Amazon Listing/ASIN risk across keywords, ads, negative reviews, forbidden words, and cross-site (US/CA/MX/EU) spread.
---

# ASIN Listing 风险监控

1. Load ASIN config.
2. For each marketplace collect keyword searchable + organic/sponsored presence.
3. Record ads on/off + spend signal.
4. Compare negative-review delta versus yesterday.
5. Scan title/bullets/A+ with the forbidden lexicon.
6. Compare US vs CA/MX/EU for change spread.
7. Output short 结论 + 行动项; missing fields = 无数据.
