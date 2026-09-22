# 2–3 minute video script

**0:00–0:20 — Question.** “I tested whether NIFTY rebounds after a significant one-day decline. I defined significant as a close-to-close loss of at least 2%, and recovery as a positive net five-session return.”

**0:20–0:50 — Data and method.** “I used a fixed Yahoo Finance NIFTY 50 daily OHLC snapshot from January 2013 to July 2026. The signal is known after the close, so entry is the next open and exit is the fifth session close. I assume 5 basis points each for cost and slippage on each side. Missing price bars are documented and windows crossing them are excluded.”

**0:50–1:20 — Events and evidence.** “In development, 62 raw signals become 44 non-overlapping events. Their average net return is −0.447%, while the median is +0.421%. A bootstrap interval for the mean crosses zero, so the positive median alone is not enough.”

**1:20–1:50 — Baseline, robustness, OOS.** “The same-period unconditional baseline averaged −0.054% net, making event excess −0.393 percentage points. The preset threshold and horizon grid has no net excess interval wholly above zero. In 2022 onward OOS, 14 events averaged +0.627% net, but the uncertainty interval remains wide.”

**1:50–2:20 — Practical interpretation.** “A conditional backtest requires positive net excess confidence bounds in both periods. That gate failed, so I did not claim a tradable strategy or publish an equity curve.”

**2:20–2:50 — Limits and conclusion.** “The sample is small, declines cluster in crises, Yahoo is a secondary vendor, and index opens are theoretical execution prices. The evidence does not support a reliable tradable rebound under this specification. The main learning is to challenge an appealing pattern with timing, a baseline, costs, and an untouched period.”

Record the actual video separately; this file is preparation material.
