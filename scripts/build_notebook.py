from pathlib import Path
import nbformat as nbf

N=nbf.v4.new_notebook
md=nbf.v4.new_markdown_cell
code=nbf.v4.new_code_cell
cells=[
md("# NIFTY decline and recovery: event study\nThe primary rule was fixed before viewing out-of-sample outcomes. This notebook reads the committed source snapshot and regenerates all outputs."),
md("## 1. Research question and hypothesis\nDoes a NIFTY close-to-close fall of at least 2% predict a positive next-open to fifth-session-close return, and a return above the same-period unconditional baseline? Positive recovery and excess performance are separate claims."),
md("## 2. Configuration\nThe threshold, holding period, per-side costs and slippage, overlap rule, and chronological split are in one immutable configuration object."),
code("from src.research import Config, load_raw, validate, opportunities, periods, select_events, analyze, robustness, run\nfrom IPython.display import display\nimport pandas as pd\ncfg=Config()\nprint(cfg)"),
md("## 3. Data loading\nThe source is the committed Yahoo Finance ^NSEI daily chart JSON. The response is pinned with a SHA-256 hash in run metadata."),
code("raw=load_raw()\nprint(raw.shape, raw.Date.min(), raw.Date.max())\ndisplay(raw.head())"),
md("## 4. Validation and cleaning\nEvery missing or impossible OHLC row is recorded. Suspicious moves are flagged and retained. Candidate event windows crossing a missing source bar are excluded."),
code("clean,checks,flags,gaps=validate(raw)\ndisplay(checks)\ndisplay(flags)\ndisplay(gaps)"),
md("## 5. Event detection\nThe signal is known only after the event day's close. Entry is at the next observed session's open; exit is at the fifth session's close. A new selected signal must occur after the prior exit. Gross and net returns retain their separate meanings."),
code("opp=opportunities(clean,cfg)\nparts=periods(opp,cfg)\nevents={k:select_events(v,cfg)[0] for k,v in parts.items()}\nfor k,v in events.items(): print(k, 'raw / selected', select_events(parts[k],cfg)[1],len(v))\ndisplay(events['development'].head())"),
md("## 6. Event analysis and statistical evidence\nThe median and tails show asymmetry obscured by the mean. Seeded event bootstrap intervals assess event means; a 20-candidate-day block bootstrap is used for the baseline mean. These intervals remain approximate because regimes and clustered crises can create further dependence."),
code("summary=pd.DataFrame([r for k,v in parts.items() for r in analyze(v,cfg,k)])\ndisplay(summary[['period','return_kind','event_n','event_mean','event_median','event_std','event_win_rate','ci_low','ci_high','p_positive']])"),
md("## 7. Baseline\nFor each chronological partition, every eligible signal date contributes the same next-open to Hth-close return. The baseline includes event dates and so represents unconditional NIFTY opportunities, not a separate regime."),
code("display(summary[['period','return_kind','baseline_n','baseline_mean','baseline_median','baseline_std','baseline_win_rate','mean_difference','excess_ci_low','excess_ci_high','p_excess']])"),
md("## 8. Robustness\nThresholds and holding periods form a predefined grid; overlap and trading drag are varied separately. Rows are diagnostic, not choices from which to pick a winning rule."),
code("rob=robustness(clean,cfg)\ndisplay(rob.loc[rob.return_kind=='net',['threshold','holding_period','overlap','cost_bps_side','slippage_bps_side','event_n','event_mean','mean_difference','excess_ci_low','excess_ci_high']])"),
md("## 9. Out-of-sample\nThe split is 2022-01-01. Development opportunities must exit before the split, while OOS signals must begin on or after it. No OOS outcome is used in the primary configuration."),
code("display(summary.loc[summary.period=='oos'])"),
md("## 10. Falsification\nCheck whether development excess is positive after costs, whether the lower confidence bound clears zero, whether overlap changes the result, and whether OOS persists. Missing-bar crossings and large crisis observations are disclosed. Many grid cells invite chance findings."),
code("regime=pd.concat([v.assign(Period=k) for k,v in events.items()],ignore_index=True)\nregime[\"Regime\"]=pd.cut(regime.EventDate.dt.year,bins=[2012,2019,2021,2026],labels=[\"2013-2019\",\"2020-2021\",\"2022-2026\"])\ndisplay(regime.groupby([\"Regime\",\"Period\"],observed=True).NetReturn.agg(n=\"size\",mean=\"mean\",median=\"median\"))\ndev_net=summary[(summary.period=='development')&(summary.return_kind=='net')].iloc[0]\noos_net=summary[(summary.period=='oos')&(summary.return_kind=='net')].iloc[0]\nprint('Development net excess:',dev_net.mean_difference,'CI:',dev_net.excess_ci_low,dev_net.excess_ci_high)\nprint('OOS net excess:',oos_net.mean_difference,'CI:',oos_net.excess_ci_low,oos_net.excess_ci_high)"),
md("## 11. Conditional backtest and conclusion\nA simple event-driven backtest is run only if both partitions have a positive lower 95% confidence bound for net excess. A weak or negative result is an investigation finding, not a strategy to optimize."),
code("result=run(cfg)\nprint('Decision and figures: results/tables/backtest_decision.json; results/figures/')")
]
nb=N(cells=cells,metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}})
Path("notebooks/event_study.ipynb").write_text(nbf.writes(nb),encoding="utf-8")
