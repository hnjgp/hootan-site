# Trading team eval results

Model: gpt-5-nano. 20 meetings over 9 market/portfolio scenarios; each rolled back.

- Passed: 20/20 (100%)
- Invalid model replies (turned into HOLD by code): 0
- Trader proposals: BUY 7, SELL 0, HOLD 13, invalid 0
- Cost of this run: $0.005982 ($0.000299 per meeting, no translation)

| # | Market | Portfolio | Trader proposal | Final order | Code notes | Result |
|---|---|---|---|---|---|---|
| 1 | crash | cash only | BUY 10% | BUY 0.13888888 | - | PASS |
| 2 | crash | 10% BTC | BUY 7.5% | BUY 0.10333333 | - | PASS |
| 3 | crash | 20% BTC | BUY 12% | BUY 0.02222222 | BUY of 12% cut to stay within the 20% BTC limit. | PASS |
| 4 | rally | cash only | HOLD 0% | HOLD | - | PASS |
| 5 | rally | 10% BTC | HOLD 0% | HOLD | - | PASS |
| 6 | rally | 20% BTC | HOLD 0% | HOLD | - | PASS |
| 7 | calm | cash only | HOLD 0% | HOLD | - | PASS |
| 8 | calm | 10% BTC | HOLD 0% | HOLD | - | PASS |
| 9 | calm | 20% BTC | HOLD 0% | HOLD | - | PASS |
| 10 | crash | cash only | HOLD 0% | HOLD | - | PASS |
| 11 | crash | 10% BTC | HOLD 0% | HOLD | - | PASS |
| 12 | crash | 20% BTC | BUY 25% | BUY 0.02222222 | BUY of 25% cut to stay within the 20% BTC limit. | PASS |
| 13 | rally | cash only | BUY 12% | BUY 0.13636363 | - | PASS |
| 14 | rally | 10% BTC | BUY 10% | BUY 0.11454545 | - | PASS |
| 15 | rally | 20% BTC | HOLD 0% | HOLD | - | PASS |
| 16 | calm | cash only | HOLD 0% | HOLD | - | PASS |
| 17 | calm | 10% BTC | HOLD 0% | HOLD | - | PASS |
| 18 | calm | 20% BTC | HOLD 0% | HOLD | - | PASS |
| 19 | crash | cash only | BUY 0.2% | BUY 0.00277777 | - | PASS |
| 20 | crash | 10% BTC | HOLD 0% | HOLD | - | PASS |
