# Trading team eval results

Model: gpt-5-nano. 20 meetings over 9 market/account scenarios on the demo exchange (open positions entered at 80,000); each rolled back.

- Passed: 20/20 (100%)
- Invalid model replies (turned into no change by code): 0
- Trader proposals: long 10, short 1, close 4, wait 5, invalid 0
- Cost of this run: $0.028723 ($0.001436 per meeting, with translation)

| # | Market | Account | Trader proposal | Final plan | Code notes | Result |
|---|---|---|---|---|---|---|
| 1 | crash | cash only | long | open long 5x with 2,000.00 USD margin, stop loss at 69,840.00 | - | PASS |
| 2 | crash | long open | wait | no change | - | PASS |
| 3 | crash | short open | close | close #3 | - | PASS |
| 4 | rally | cash only | long | open long 3x with 500.00 USD margin, stop loss at 86,240.00 | - | PASS |
| 5 | rally | long open | long | open long 3x with 522.39 USD margin, stop loss at 86,240.00, take profit at 93,280.00 | - | PASS |
| 6 | rally | short open | long | close #7; open long 5x with 1,909.55 USD margin, stop loss at 86,240.00, take profit at 92,400.00 | - | PASS |
| 7 | calm | cash only | long | open long 5x with 2,000.00 USD margin, stop loss at 78,400.00 | - | PASS |
| 8 | calm | long open | close | close #10 | - | PASS |
| 9 | calm | short open | long | close #11; open long 4x with 1,999.55 USD margin, stop loss at 78,400.00, take profit at 81,600.00 | Margin of 25% cut to the 20% of equity limit. | PASS |
| 10 | crash | cash only | long | open long 3x with 500.00 USD margin, stop loss at 69,840.00, take profit at 77,760.00 | - | PASS |
| 11 | crash | long open | wait | no change | - | PASS |
| 12 | crash | short open | wait | no change | - | PASS |
| 13 | rally | cash only | long | open long 5x with 500.00 USD margin, stop loss at 86,240.00, take profit at 93,280.00 | - | PASS |
| 14 | rally | long open | close | close #17 | - | PASS |
| 15 | rally | short open | close | close #18 | - | PASS |
| 16 | calm | cash only | long | open long 5x with 2,000.00 USD margin, stop loss at 77,600.00 | - | PASS |
| 17 | calm | long open | short | open short 4x with 199.96 USD margin, stop loss at 81,600.00 | - | PASS |
| 18 | calm | short open | long | close #22; open long 5x with 499.89 USD margin, stop loss at 78,400.00 | - | PASS |
| 19 | crash | cash only | wait | no change | - | PASS |
| 20 | crash | long open | wait | no change | - | PASS |
