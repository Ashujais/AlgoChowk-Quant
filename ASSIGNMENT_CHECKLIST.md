# Assignment Checklist

Status reflects the pinned 2026-09-22 source snapshot and default configuration. “N/A” means the predeclared trading-evidence gate failed; it is not an omitted positive backtest.

| Requirement | Implemented? | Location | Verification |
|---|---|---|---|
| NIFTY historical data sourced, source documented, dates, OHLC | Yes | data/raw; data/README.md | SHA-256 and 2013-01-02–2026-07-07 in run_metadata.json |
| Missing dates and market gaps | Yes, calendar caveat | src/research.py; validation_report.csv; calendar_gaps.csv | 207 absent weekdays include holidays; 8 long gaps classified: 1 source-quality, 7 holiday-unverified |
| Duplicate dates/rows and ordering | Yes | src/research.py; validation_report.csv | 0 duplicates and 0 wrong-order transitions |
| Missing/invalid OHLC and impossible relationships | Yes | src/research.py; validation_flags.csv | 18 missing OHLC rows excluded; invalid relationship count 0 |
| Suspicious observations | Yes | validation_flags.csv; data/README.md | 4 unusual rows flagged and retained |
| Event, recovery, entry, exit, holding period | Yes | Config, opportunities; RESEARCH_NOTE.md | −2%, next open, fifth session close; event-level CSV |
| Costs and slippage | Yes | Config, opportunities; RESEARCH_NOTE.md | 5 bps each per side; synthetic cost test |
| Event-level dates, prices, gross and net returns | Yes | event_results.csv | 58 selected events across periods |
| Mean, median, win rate, volatility, distribution, percentiles | Yes | summary_statistics.csv; figures | Separate gross/net and period rows |
| Statistical evidence | Yes | statistics functions in src/research.py; summary_statistics.csv | Seeded 95% bootstrap CIs and one-sided p-values |
| Same-period baseline | Yes | analyze; summary_statistics.csv | 2,117 development and 1,083 OOS eligible days |
| Threshold and holding-period robustness | Yes | robustness_results.csv; sensitivity.png | 3 thresholds × 4 horizons |
| Overlap, costs, slippage robustness | Yes | robustness_results.csv | all/nonoverlap and zero/primary/high drag |
| Data snooping, multiple testing, post-hoc selection, overfitting | Yes | README.md; RESEARCH_NOTE.md | No best grid row selected |
| Chronological OOS split and results | Yes | Config, periods; oos_results.csv | 2022-01-01; 44 development / 14 OOS selected |
| Falsification and rejection criteria | Yes | RESEARCH_NOTE.md; README.md; notebook | Applied to timing, costs, sample, overlap, regimes, quality, sensitivity, non-stationarity |
| Look-ahead and source-bar analysis | Yes | opportunities; tests/test_research.py | Eight synthetic tests; signal < entry <= exit |
| Simple event-driven backtest | Conditional, not run | backtest function; backtest_decision.json | Net-excess evidence gate failed in both partitions |
| Backtest entry/exit, costs, trades, equity, drawdown | Implemented conditionally | src/research.py | No trading performance claimed or plotted |
| NIFTY price, event, distribution, baseline, robustness figures | Yes | results/figures | Five generated PNG files |
| Research Note <= 2 pages | Yes by concise length | RESEARCH_NOTE.md | Approx. 550 words; review final renderer if exporting |
| README and reproducibility commands | Yes | README.md | Pinned raw snapshot; exact commands |
| AI Usage Note <= 1 page | Yes by concise length | AI_USAGE_NOTE.md | Approx. 230 words; no human decisions fabricated |
| 2–3 minute video preparation | Yes | VIDEO_SCRIPT.md | Timed 0:00–2:50 script; actual recording remains manual |
| Notebook | Yes | notebooks/event_study.ipynb | Narrative order and execution script |
| Tests | Yes | tests/test_research.py | 8 passed |
| No fabricated results | Yes | raw JSON; generated tables; run_metadata.json | All stated numbers checked against CSV output |
| GitHub submission | Manual | local project | Create/push remote repository and record video before submission |
