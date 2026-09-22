import numpy as np
import pandas as pd
import pytest
from src.research import Config,validate,opportunities,select_events,max_drawdown,backtest

def sample():
    dates=pd.bdate_range("2024-01-01",periods=9)
    close=[100,97,98,95,96,97,99,100,101]
    open_=[100,99,97.5,97,95.5,96,97.5,99,100]
    return pd.DataFrame({"Date":dates,"Open":open_,"High":np.maximum(open_,close)+1,
                         "Low":np.minimum(open_,close)-1,"Close":close,"SourceRow":range(9)})

def test_event_return_entry_exit_and_cost():
    x=sample()
    o=opportunities(x,Config(holding_period=3,cost_bps_per_side=5,slippage_bps_per_side=5))
    first=o.iloc[0]
    assert first.EventReturn==pytest.approx(-.03)
    assert first.EntryDate==x.Date.iloc[2] and first.ExitDate==x.Date.iloc[4]
    assert first.EntryPrice==x.Open.iloc[2] and first.ExitPrice==x.Close.iloc[4]
    assert first.ForwardReturn==pytest.approx(96/97.5-1)
    assert first.NetReturn==pytest.approx(96*.999/(97.5*1.001)-1)
    assert first.NetReturn<first.ForwardReturn

def test_nonoverlap():
    o=opportunities(sample(),Config(threshold=-.02,holding_period=3))
    e,n=select_events(o,Config(threshold=-.02,holding_period=3))
    assert n==2 and len(e)==1
    all_e,_=select_events(o,Config(threshold=-.02,holding_period=3,overlap="all"))
    assert len(all_e)==2

def test_missing_source_bar_cannot_bridge():
    x=sample()
    x.loc[3:,"SourceRow"]+=1
    o=opportunities(x,Config(holding_period=3))
    assert 1 not in o.EventIndex.values

def test_validation_flags_and_removes_only_unusable():
    x=sample().drop(columns="SourceRow")
    x.loc[2,"Open"]=np.nan
    clean,report,flags,gaps=validate(x)
    assert len(clean)==8
    assert dict(zip(report.Check,report.Value))["missing_ohlc_rows"]==1
    assert "missing OHLC" in flags.Reason.values
    assert clean.Date.is_monotonic_increasing

def test_duplicate_and_impossible_ohlc():
    x=sample().drop(columns="SourceRow")
    x.loc[2,"High"]=1
    x=pd.concat([x,x.iloc[[3]]],ignore_index=True)
    clean,report,_,_=validate(x)
    d=dict(zip(report.Check,report.Value))
    assert d["duplicate_date_rows"]==2 and d["invalid_ohlc_rows"]==1
    assert len(clean)==7

def test_drawdown():
    assert max_drawdown(pd.Series([1,1.2,.9,1.1]))==pytest.approx(-.25)

def test_config_rejects_bad_inputs():
    with pytest.raises(ValueError):
        Config(holding_period=0)


def test_conditional_backtest_marks_daily_equity():
    x=sample()
    cfg=Config(holding_period=3)
    event=opportunities(x,cfg).iloc[[0]]
    eq,metrics=backtest(event,x,cfg)
    assert metrics["number_trades"]==1
    assert metrics["total_return"]==pytest.approx(event.NetReturn.iloc[0])
    assert eq.loc[x.Date.iloc[2]]!=eq.loc[x.Date.iloc[1]]
    assert metrics["max_drawdown"]<=0
