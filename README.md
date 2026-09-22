# NIFTY 50 Decline and Recovery: Event Study

## Research Question
Does NIFTY 50 tend to recover after a significant one-day fall?

## Hypothesis
A close-to-close fall of at least 2% is followed by a positive net next-open to fifth-session-close return, and that return exceeds unconditional NIFTY forward returns over the same chronological period. Positive recovery and excess return are separate tests. The primary rule was fixed before examining OOS outcomes; this is a research investigation, not parameter optimization.

## Methodology
The signal is available only after the event close. Candidate events are filtered chronologically so that a new event is selected only after the prior exit. Raw and filtered counts are both reported. All eligible dates in each period form the unconditional baseline. Development opportunities exit before 2022-01-01; OOS signals start on or after it, with no outcome crossing the boundary. Gross and net returns are separate. For every event, the CSV records event/entry/exit dates and prices, holding period, and both returns.

## Data Source
[Yahoo Finance NIFTY 50 history](https://finance.yahoo.com/quote/%5ENSEI/history/), symbol `^NSEI` (daily NIFTY 50 price-index OHLC). The exact chart URL, access date, SHA-256, and source caveats are in [data/README.md](data/README.md). A fixed raw JSON snapshot is committed, so the main run needs no network.

## Data Range
2013-01-02 through 2026-07-07: 3,337 source rows; 3,319 after excluding 18 rows with missing OHLC. Development has 2,117 eligible five-session opportunities; OOS has 1,083.

## Data Cleaning
No price interpolation, return winsorization, or silent outlier deletion. The 18 excluded rows and four retained suspicious observations are listed in `results/tables/validation_flags.csv`. Price windows crossing an excluded source bar are omitted. The validation report also checks duplicate dates/rows, ordering, missing/invalid prices, OHLC relationships, missing weekdays, and long gaps. Missing weekdays include exchange holidays; the vendor response cannot by itself certify the official market calendar. Of eight long gaps, one contains a missing-OHLC source row and seven remain holiday-unverified.

## Event Definition
Daily close divided by previous observed close minus one is at most −2%. The threshold is configurable. Events are selected non-overlapping by default; an `all` setting reports the dependent raw sample.

## Recovery Definition
The event's net entry-to-exit return is positive. A second test asks whether its mean exceeds the unconditional same-period mean.

## Entry / Exit
Event identified at close; buy at the next observed session's open; sell at the fifth subsequent session's close. The entry session counts as session 1. Timing and missing-source-bar guards have synthetic tests.

## Holding Period
Five sessions primary; 1, 3, 5, and 10 sessions are predeclared sensitivity checks. No horizon was selected for a favorable result.

## Transaction Costs / Slippage
5 basis points of transaction costs plus 5 basis points of slippage **per side**, or 10 bps per side total. Net return is exit × (1−0.001) / [entry × (1+0.001)] − 1. Zero and 20 bps per side total are also checked. These are modeling assumptions, not measured execution.

## Statistical Methods
Descriptive mean, median, sample standard deviation, win rate, minimum, maximum, and 5th/25th/75th/95th percentiles. A seeded 3,000-draw percentile bootstrap resamples selected non-overlapping events for event means; baseline means use circular 20-candidate-day blocks because forward returns overlap. One-sided centered bootstrap p-values test mean > 0 and event-minus-baseline mean > 0; 95% intervals give uncertainty. Event clustering across crises can still make intervals optimistic. Statistical significance would not prove tradeable profit or causality.

## Baseline
For each partition and holding period, **every** eligible NIFTY date has the same next-open to Hth-close calculation, including costs and event dates. This avoids a different historical regime or execution convention. Event-vs-baseline mean, median, volatility, win rate, full descriptive distribution, and mean excess appear in the summary CSV.

## Robustness
The development grid covers thresholds −1.5%, −2%, −2.5% and horizons 1, 3, 5, 10. Separate rows vary overlap and costs/slippage. Means change sign across specifications; no grid row has a net excess 95% interval entirely above zero. Multiple testing, data snooping, post-hoc selection, and overfitting mean an attractive row would be exploratory, not proof.

## Out-of-Sample Validation
Fixed split: 2022-01-01. Development: 62 raw / 44 selected primary events. OOS: 19 raw / 14 selected. The primary specification and conditional backtest evidence gate were fixed before reading OOS returns. OOS event mean net return is +0.627%, but its median is −0.347% and mean-excess confidence interval crosses zero. It does not independently confirm a dependable recovery.

## Backtest
The simple conditional event-driven backtest implementation is in `src/research.py` (entry, exit, costs, trade count, equity, drawdown). The predeclared gate requires the **lower** 95% net-excess bound to exceed zero in both development and OOS. It failed. Thus no strategy equity, cumulative performance, or drawdown is presented as a trading result; see `backtest_decision.json`. The index itself is not directly executable.

## Results
Primary five-session **net** results; returns are percentages of the entry price:

| Period | Selected events | Event mean | Median | Win rate | Baseline mean | Mean excess | 95% excess CI | One-sided p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Development | 44 | −0.447% | +0.421% | 52.3% | −0.054% | −0.393 pp | [−1.594, +0.685] pp | 0.749 |
| OOS | 14 | +0.627% | −0.347% | 42.9% | −0.088% | +0.715 pp | [−0.858, +2.396] pp | 0.188 |

The development event mean 95% interval is [−1.610%, +0.627%], with p = 0.785 for a positive net mean. See the machine-readable CSVs for exact values, gross figures, volatility, percentiles, and all robustness rows. The final interpretation is **insufficient evidence for a reliable tradable rebound under the primary specification**.

## Limitations
Only 44 development and 14 OOS selected events. A regime check finds mean net return +0.035% for 27 selected 2013–2019 events, versus −1.214% for 17 in 2020–2021 (see regime_results.csv); crisis clustering and non-stationarity are material. Yahoo is a secondary vendor with missing bars, and no official holiday reconciliation has been performed. The NIFTY price index is not directly tradable, excludes dividends, and does not capture ETF/futures tracking, financing, taxes, liquidity, or impact. The bootstrap approximates dependence. The threshold/horizon grid is diagnostic and cannot establish a discovery after multiple testing. Rejection evidence for the original claim is negative net excess or confidence bounds that fail to clear zero in either period, instability under costs/overlap, or material correction of source prices; several are already observed.

## Reproducibility
From the repository root on Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.research
python scripts/build_notebook.py
python scripts/run_notebook.py
```

The raw JSON is included. `python -m src.research --help` shows configurable flags for threshold, holding period, costs, slippage, overlap, and split date. Run the default command to reproduce the reported primary result. Tables are in `results/tables/`; plots are in `results/figures/`. The notebook is a readable research narrative and re-executes the default pipeline. A different configuration overwrites output files; rerun defaults before comparing with this README.

## Installation
Use the venv and pip commands above. The requirements file lists runtime, plotting, testing, and notebook packages.

## Usage
```powershell
python -m src.research
python -m src.research --threshold -0.015 --holding-period 3 --cost-bps-per-side 10 --slippage-bps-per-side 10 --overlap all --split-date 2022-01-01
```

## Project Structure
`data/raw`: pinned source; `data/processed`: validated CSV; `src/research.py`: engine; `tests/`: synthetic checks; `notebooks/`: narrative; `results/tables` and `results/figures`: generated evidence; `RESEARCH_NOTE.md`, `AI_USAGE_NOTE.md`, `VIDEO_SCRIPT.md`, `ASSIGNMENT_CHECKLIST.md`: submission support.

## Testing
`python -m pytest -q` tests return arithmetic, signal and execution timing, cost drag, overlap, missing-bar handling, data validation, and drawdown. The full pipeline regenerates the validation report and research outputs.

## AI Usage
See [AI_USAGE_NOTE.md](AI_USAGE_NOTE.md). The note identifies the agent's actual contributions, a test-discovered code error, and the assumptions the applicant should review. The video script is provided; recording and GitHub publication are manual submission steps.
