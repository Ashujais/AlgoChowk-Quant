# Data provenance and cleaning

The included raw snapshot is `raw/nifty50_yahoo_2013_2026.json`, downloaded **2026-09-22** from [Yahoo Finance NIFTY 50 historical prices](https://finance.yahoo.com/quote/%5ENSEI/history/) via:

`https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?period1=1356998400&period2=1783468800&interval=1d&events=history`

Instrument: NIFTY 50 **price index** (`^NSEI`), daily OHLC in index points, local dates converted from response timestamps to Asia/Kolkata. Raw SHA-256: `791448910a6895907e44c4ef2a38490afa03baea6abd0e8eb712bc136973373d`. The fixed snapshot eliminates dependence on future vendor revisions or network access. Use `python -m src.research` to rebuild `processed/nifty50_daily.csv`.

Raw coverage: 2013-01-02 to 2026-07-07, 3,337 rows. Eighteen rows have all OHLC missing and are excluded from price calculations; dates/reasons are recorded in `../results/tables/validation_flags.csv`. This includes market holidays/special dates and some apparent trading dates. A candidate window is excluded if it crosses one of those missing source rows, preventing a shorter actual holding period from being labelled five observed sessions. Four large-return/range observations are retained and flagged. There were no duplicate dates, ordering errors, or invalid price relationships. Of 207 absent weekdays, many are holidays; the vendor response alone cannot certify the official exchange calendar. Eight gaps exceed four calendar days and are itemized in `calendar_gaps.csv`: one contains a missing-OHLC source row; seven have unverified holiday status. No interpolation, forward fill, or winsorization is applied.

Limitations: Yahoo is a secondary vendor; some missing dates and historical corrections may differ from NSE Indices. Index values are not directly executable, and this price index omits dividends, financing, and tracking error. [NSE Indices historical reports](https://www.niftyindices.com/reports) are the official cross-check source.
