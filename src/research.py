from __future__ import annotations
import argparse, hashlib, json
from dataclasses import dataclass, replace
from pathlib import Path
import numpy as np
import pandas as pd


RAW = Path("data/raw/nifty50_yahoo_2013_2026.json")
TABLES = Path("results/tables")
FIGURES = Path("results/figures")

@dataclass(frozen=True)
class Config:
    threshold: float = -0.02
    holding_period: int = 5
    cost_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 5.0
    overlap: str = "nonoverlap"
    split_date: str = "2022-01-01"
    bootstrap_draws: int = 3000
    seed: int = 20260922
    def __post_init__(self):
        if not -1 < self.threshold < 0 or self.holding_period < 1:
            raise ValueError("Invalid threshold or holding period")
        if self.overlap not in ("all", "nonoverlap"):
            raise ValueError("Invalid overlap rule")
        if min(self.cost_bps_per_side, self.slippage_bps_per_side) < 0:
            raise ValueError("Negative trading drag")

def load_raw(path: Path = RAW) -> pd.DataFrame:
    obj = json.loads(path.read_text(encoding="utf-8"))["chart"]["result"][0]
    if obj["meta"]["symbol"] != "^NSEI" or obj["meta"]["instrumentType"] != "INDEX":
        raise ValueError("Unexpected instrument")
    q = obj["indicators"]["quote"][0]
    dates = pd.to_datetime(obj["timestamp"], unit="s", utc=True).tz_convert("Asia/Kolkata").date
    return pd.DataFrame({"Date": pd.to_datetime(dates), **{k.title(): q[k] for k in ("open","high","low","close")}})

def validate(raw: pd.DataFrame):
    needed = ["Date","Open","High","Low","Close"]
    if set(needed)-set(raw):
        raise ValueError("Missing required columns")
    x = raw.copy()
    x["SourceRow"] = np.arange(len(x))
    x["Date"] = pd.to_datetime(x.Date, errors="coerce")
    for c in needed[1:]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    missing = x[needed[1:]].isna().any(axis=1)
    bad = (x[needed[1:]] <= 0).any(axis=1) | (x.High < x.Low) | (x.Open < x.Low-0.01) | (x.Open > x.High+0.01) | (x.Close < x.Low-0.01) | (x.Close > x.High+0.01)
    duplicate = x.Date.duplicated(keep=False)
    exact = x.duplicated(keep=False)
    invalid_date = x.Date.isna()
    excluded = missing | bad | duplicate | invalid_date
    clean = x.loc[~excluded].sort_values("Date").reset_index(drop=True)
    clean["CloseReturn"] = clean.Close.pct_change(fill_method=None)
    suspect = clean.CloseReturn.abs().gt(.08) | (clean.High/clean.Low-1).gt(.10)
    gap = clean.Date.diff().dt.days
    gaps = clean.loc[gap.gt(4),["Date"]].copy()
    gaps["PreviousDate"] = clean.Date.shift(1)[gap.gt(4)].values
    gaps["CalendarDays"] = gap[gap.gt(4)].values
    gaps["MissingOHLCSourceRows"] = [int(((x.Date>r.PreviousDate)&(x.Date<r.Date)&missing).sum()) for r in gaps.itertuples()]
    gaps["Classification"] = np.where(gaps.MissingOHLCSourceRows>0,"data-quality: source row lacks OHLC","calendar gap: holiday status unverified")
    flags = x.loc[excluded,needed].copy()
    flags["Reason"] = np.select([missing[excluded],bad[excluded],duplicate[excluded],invalid_date[excluded]],["missing OHLC","invalid OHLC","duplicate date","invalid date"],default="")
    retained = clean.loc[suspect,needed+["CloseReturn"]].copy()
    retained["Reason"] = "large close return >8% or intraday range >10%; retained"
    flags = pd.concat([flags,retained],ignore_index=True)
    checks = {
        "raw_rows":len(x), "date_min":str(x.Date.min().date()),"date_max":str(x.Date.max().date()),
        "wrong_order_transitions":int((x.Date.diff().dt.days<0).sum()),
        "invalid_dates":int(invalid_date.sum()),"duplicate_date_rows":int(duplicate.sum()),
        "exact_duplicate_rows":int(exact.sum()),"missing_ohlc_rows":int(missing.sum()),
        "invalid_ohlc_rows":int(bad.sum()),"excluded_rows":int(excluded.sum()),
        "clean_rows":len(clean),
        "absent_weekdays_including_holidays":len(pd.bdate_range(clean.Date.min(),clean.Date.max()).difference(clean.Date)),
        "gaps_over_four_calendar_days":len(gaps),"long_gaps_with_missing_source_row":int((gaps.MissingOHLCSourceRows>0).sum()),"suspicious_retained_rows":int(suspect.sum())
    }
    return clean,pd.DataFrame(checks.items(),columns=["Check","Value"]),flags,gaps

def opportunities(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    h=cfg.holding_period
    rows=[]
    for i in range(1,len(df)-h):
        if "SourceRow" in df and df.SourceRow.iloc[i+h]-df.SourceRow.iloc[i-1] != h+1:
            continue  # missing source bars must not shorten the holding period
        signal,entry,exit_date=df.Date.iloc[i],df.Date.iloc[i+1],df.Date.iloc[i+h]
        assert signal < entry <= exit_date
        ep,xp=float(df.Open.iloc[i+1]),float(df.Close.iloc[i+h])
        drag=(cfg.cost_bps_per_side+cfg.slippage_bps_per_side)/10000
        rows.append((i,signal,df.Close.iloc[i]/df.Close.iloc[i-1]-1,entry,ep,exit_date,xp,h,xp/ep-1,xp*(1-drag)/(ep*(1+drag))-1))
    return pd.DataFrame(rows,columns=["EventIndex","EventDate","EventReturn","EntryDate","EntryPrice","ExitDate","ExitPrice","HoldingPeriod","ForwardReturn","NetReturn"])

def periods(opp: pd.DataFrame,cfg: Config):
    split=pd.Timestamp(cfg.split_date)
    return {"development":opp.loc[opp.ExitDate<split].copy(),
            "oos":opp.loc[opp.EventDate>=split].copy()}

def select_events(opp: pd.DataFrame,cfg: Config):
    raw=opp.loc[opp.EventReturn<=cfg.threshold].copy()
    if cfg.overlap=="all":
        return raw.reset_index(drop=True),len(raw)
    chosen=[]
    last_exit=-1
    for row in raw.itertuples():
        if row.EventIndex>last_exit:
            chosen.append(row.Index)
            last_exit=row.EventIndex+cfg.holding_period
    return raw.loc[chosen].reset_index(drop=True),len(raw)

def describe(s: pd.Series):
    a=s.dropna().to_numpy(float)
    if not len(a):
        return {k:np.nan for k in ("n","mean","median","std","win_rate","min","p05","p25","p75","p95","max")}
    return dict(n=len(a),mean=a.mean(),median=np.median(a),std=a.std(ddof=1) if len(a)>1 else np.nan,
                win_rate=(a>0).mean(),min=a.min(),p05=np.quantile(a,.05),p25=np.quantile(a,.25),
                p75=np.quantile(a,.75),p95=np.quantile(a,.95),max=a.max())

def bootstrap(e: pd.Series,b: pd.Series,cfg: Config):
    """Event-resampling and 20-day circular block baseline; one-sided centered bootstrap p."""
    a=e.to_numpy(float); base=b.to_numpy(float)
    if len(a)<2 or len(base)<2:
        return dict(ci_low=np.nan,ci_high=np.nan,p_positive=np.nan,excess_ci_low=np.nan,excess_ci_high=np.nan,p_excess=np.nan)
    rng=np.random.default_rng(cfg.seed)
    draws=cfg.bootstrap_draws
    em=a[rng.integers(len(a),size=(draws,len(a)))].mean(axis=1)
    starts=rng.integers(len(base),size=(draws,int(np.ceil(len(base)/20))))
    bm=base[(starts[:,:,None]+np.arange(20))%len(base)].reshape(draws,-1)[:,:len(base)].mean(axis=1)
    delta=em-bm
    observed=a.mean()-base.mean()
    return dict(ci_low=np.quantile(em,.025),ci_high=np.quantile(em,.975),
                p_positive=(1+(em-a.mean()>=a.mean()).sum())/(draws+1),
                excess_ci_low=np.quantile(delta,.025),excess_ci_high=np.quantile(delta,.975),
                p_excess=(1+(delta-observed>=observed).sum())/(draws+1))

def analyze(opp: pd.DataFrame,cfg: Config,label: str):
    events,raw_n=select_events(opp,cfg)
    # All eligible dates in the same chronological partition, same next-open to Hth-close window.
    base=opp
    for kind,col in (("gross","ForwardReturn"),("net","NetReturn")):
        ed,bd=describe(events[col]),describe(base[col])
        evidence=bootstrap(events[col],base[col],cfg)
        yield {"period":label,"return_kind":kind,"threshold":cfg.threshold,"holding_period":cfg.holding_period,
               "overlap":cfg.overlap,"cost_bps_side":cfg.cost_bps_per_side,"slippage_bps_side":cfg.slippage_bps_per_side,
               "raw_events":raw_n,"eligible_days":len(base),
               **{"event_"+k:v for k,v in ed.items()},**{"baseline_"+k:v for k,v in bd.items()},
               "mean_difference":ed["mean"]-bd["mean"],"median_difference":ed["median"]-bd["median"],
               "win_rate_difference":ed["win_rate"]-bd["win_rate"],**evidence}

def robustness(opp,cfg):
    rows=[]
    specs=[]
    for t in (-.015,-.02,-.025):
        for h in (1,3,5,10):
            specs.append(replace(cfg,threshold=t,holding_period=h))
    specs += [replace(cfg,overlap="all"),
              replace(cfg,cost_bps_per_side=0,slippage_bps_per_side=0),
              replace(cfg,cost_bps_per_side=10,slippage_bps_per_side=10)]
    for spec in specs:
        sample=periods(opportunities(opp,spec),spec)["development"]
        rows += list(analyze(sample,spec,"development"))
    return pd.DataFrame(rows)

def max_drawdown(equity: pd.Series) -> float:
    return float((equity/equity.cummax()-1).min())

def backtest(events: pd.DataFrame,df: pd.DataFrame,cfg: Config):
    """Cash while idle; mark each open trade at daily closes, with modeled entry/exit drag."""
    eq=pd.Series(1.0,index=df.Date,name="Equity")
    current=1.0
    drag=(cfg.cost_bps_per_side+cfg.slippage_bps_per_side)/10000
    trades=[]
    for row in events.sort_values("EntryDate").itertuples():
        mask=(df.Date>=row.EntryDate)&(df.Date<=row.ExitDate)
        marked=df.loc[mask,["Date","Close"]]
        eq.loc[marked.Date]=current*marked.Close.to_numpy()/(row.EntryPrice*(1+drag))
        current=current*(1+row.NetReturn)
        eq.loc[row.ExitDate]=current
        eq.loc[eq.index>row.ExitDate]=current
        trades.append(row.NetReturn)
    daily=eq.pct_change().dropna()
    years=(eq.index[-1]-eq.index[0]).days/365.25
    return eq,dict(total_return=current-1,annualized_return=current**(1/years)-1 if years>0 else np.nan,
                   number_trades=len(trades),win_rate=float(np.mean(np.array(trades)>0)) if trades else np.nan,
                   average_trade=float(np.mean(trades)) if trades else np.nan,
                   annualized_volatility=float(daily.std(ddof=1)*np.sqrt(252)),max_drawdown=max_drawdown(eq))

def plots(df,events,dev,oos,rob,backtest_equity=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGURES.mkdir(parents=True,exist_ok=True)
    def save(name):
        plt.tight_layout();plt.savefig(FIGURES/name,dpi=150);plt.close()
    plt.figure(figsize=(10,4));plt.plot(df.Date,df.Close,lw=1);plt.scatter(events.EventDate,df.set_index("Date").loc[events.EventDate,"Close"],s=8,color="crimson");plt.title("NIFTY 50 price and primary event dates");plt.ylabel("Index points");save("price_events.png")
    plt.figure(figsize=(7,4));plt.hist(events.EventReturn*100,bins=25);plt.title("Event-day close-to-close returns");plt.xlabel("%");save("event_declines.png")
    plt.figure(figsize=(7,4));plt.hist(events.ForwardReturn*100,bins=25);plt.title("Primary forward returns");plt.xlabel("%");save("forward_distribution.png")
    plt.figure(figsize=(7,4));plt.boxplot([events.loc[events.Period=="development","NetReturn"]*100,dev.NetReturn*100,events.loc[events.Period=="oos","NetReturn"]*100,oos.NetReturn*100],tick_labels=["Dev event","Dev baseline","OOS event","OOS baseline"],showfliers=True);plt.title("Net forward returns: events vs same-period baseline");plt.ylabel("%");save("baseline_boxplot.png")
    p=rob.loc[(rob.return_kind=="net") & (rob.overlap=="nonoverlap") & (rob.cost_bps_side==5) & (rob.slippage_bps_side==5)]
    plt.figure(figsize=(7,4))
    for t,g in p.groupby("threshold"):
        plt.plot(g.holding_period,g.event_mean*100,marker="o",label=f"{t:.1%} threshold")
    plt.axhline(0,color="gray",lw=.7);plt.title("Development sensitivity: mean net event return");plt.xlabel("Holding sessions");plt.ylabel("%");plt.legend();save("sensitivity.png")
    if backtest_equity is not None:
        plt.figure(figsize=(9,4));plt.plot(backtest_equity.index,backtest_equity.values);plt.title("Conditional event-driven equity");save("backtest_equity.png")
        plt.figure(figsize=(9,4));plt.plot(backtest_equity.index,backtest_equity/backtest_equity.cummax()-1);plt.title("Conditional drawdown");save("backtest_drawdown.png")

def run(cfg=Config()):
    TABLES.mkdir(parents=True,exist_ok=True)
    raw=load_raw()
    df,validation,flags,gaps=validate(raw)
    if len(df)<500:
        raise ValueError("Insufficient clean history")
    validation.to_csv(TABLES/"validation_report.csv",index=False)
    flags.to_csv(TABLES/"validation_flags.csv",index=False)
    gaps.to_csv(TABLES/"calendar_gaps.csv",index=False)
    df.to_csv("data/processed/nifty50_daily.csv",index=False)
    opp=opportunities(df,cfg)
    sections=periods(opp,cfg)
    events={k:select_events(v,cfg)[0] for k,v in sections.items()}
    event_table=pd.concat([v.assign(Period=k) for k,v in events.items()],ignore_index=True)
    event_table.to_csv(TABLES/"event_results.csv",index=False)
    regime=event_table.assign(Regime=pd.cut(event_table.EventDate.dt.year,bins=[2012,2019,2021,2026],labels=["2013-2019","2020-2021","2022-2026"]))
    regime.groupby(["Regime","Period"],observed=True).NetReturn.agg(n="size",mean="mean",median="median",win_rate=lambda v:(v>0).mean()).reset_index().to_csv(TABLES/"regime_results.csv",index=False)
    summary=pd.DataFrame([r for k,v in sections.items() for r in analyze(v,cfg,k)])
    summary.to_csv(TABLES/"summary_statistics.csv",index=False)
    robust=robustness(df,cfg)
    robust.to_csv(TABLES/"robustness_results.csv",index=False)
    summary.loc[summary.period=="oos"].to_csv(TABLES/"oos_results.csv",index=False)
    # Tradability gate was fixed before OOS inspection: both partitions' net excess CI lower > 0.
    gate=bool((summary.loc[summary.return_kind=="net","excess_ci_low"]>0).all())
    bt=None; metrics={"backtest_executed":gate,"gate":"both development and OOS net-excess 95% CI lower bounds > 0"}
    if gate:
        bt,extra=backtest(event_table,df,cfg);metrics.update(extra)
        bt.to_csv(TABLES/"backtest_equity.csv")
    (TABLES/"backtest_decision.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    plots(df,event_table,sections["development"],sections["oos"],robust,bt)
    meta=dict(config=cfg.__dict__,raw_sha256=hashlib.sha256(RAW.read_bytes()).hexdigest(),validation={r.Check:r.Value for r in validation.itertuples()},backtest=metrics)
    (TABLES/"run_metadata.json").write_text(json.dumps(meta,indent=2,default=str),encoding="utf-8")
    print(summary.to_string(index=False,float_format=lambda x:f"{x:.6f}"))
    print("Backtest:",metrics)
    return summary

def main():
    p=argparse.ArgumentParser()
    for name,t,default in (("threshold",float,-.02),("holding-period",int,5),("cost-bps-per-side",float,5),("slippage-bps-per-side",float,5),("overlap",str,"nonoverlap"),("split-date",str,"2022-01-01")):
        p.add_argument("--"+name,type=t,default=default)
    a=p.parse_args()
    run(Config(threshold=a.threshold,holding_period=a.holding_period,cost_bps_per_side=a.cost_bps_per_side,slippage_bps_per_side=a.slippage_bps_per_side,overlap=a.overlap,split_date=a.split_date))
if __name__=="__main__":
    main()
