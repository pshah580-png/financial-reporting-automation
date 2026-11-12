# Financial Reporting Automation

> **Data note:** Everything in this repository uses **synthetic demo data — created for portfolio demonstration; not employer data.** Accounts, tickers and trades are fictional. The effort comparison below is a demo scenario for illustration — it is not a measured result from a real employer.

## The business problem

Recurring financial reporting — daily trade summaries, account activity, positions snapshots — is often assembled by hand: export, copy, format, check, send, every business day. It is slow, it is error-prone in exactly the same places every time, and when something looks wrong there is no record of what was produced, when, or from which data.

This project automates that cycle end to end and, just as importantly, proves each run happened correctly.

## What it does

1. **Loads** the day's trades, positions and the report schedule (`data/report_schedule.csv`) into SQLite.
2. **Generates** each scheduled report as a clean CSV using the commented queries in `sql/report_extracts.sql`: daily trade summary, account activity summary, positions snapshot — plus a plain-English summary of the latest day.
3. **Controls** the run: report totals are tied back to a control total computed independently from the raw trades. A mismatch is logged as `FAILED`, never silently released.
4. **Audits** every run: `output/audit_log.csv` records the timestamp, rows read, files written, control total and status — the trail a reviewer or auditor actually asks for.

## Demo-scenario effort framing (illustrative, synthetic data)

| | Manual (demo scenario) | Automated (this project) |
|---|---|---|
| Daily effort | ~45 min of export / format / check / send | ~2 min reviewing the audit log |
| Evidence of the run | Email sent-items, if you're lucky | Timestamped audit log with control total |
| Error detection | Whoever spots it first | Control check fails the run loudly |

## How to run

```bash
python python/generate_reports.py    # stdlib only, nothing to install
```

Outputs land in `output/`: the three report CSVs, `latest_day_summary.txt`, and `audit_log.csv` (a sample from a verified demo run is included).

**Scheduling (concept):** the script is designed to be run by any scheduler — e.g. cron `30 6 * * 1-5` for 06:30 on business days, Windows Task Scheduler, or an orchestrator such as Airflow. It takes no arguments and exits non-zero if the control check fails, so a scheduler can alert on failure.

## Repository layout

- `data/` — synthetic CSVs: `trades.csv`, `positions.csv`, `report_schedule.csv`
- `sql/` — commented extract/aggregation + control-total queries
- `python/` — `generate_reports.py`: load → generate → control-check → audit-log
- `output/` — sample generated reports, summary and audit log from a real run of the script on the synthetic data

## Skills demonstrated

Python automation (stdlib `sqlite3`/`csv`, deterministic report generation) · SQL (aggregation, `CASE` pivots, control totals) · Reporting controls & audit trails · Scheduling concepts (cron, exit-code alerting) · Financial-services domain knowledge (trades, positions, settlement, notional)

## Author

Priyanka Shah — Senior Data / BI Analyst · [Tableau Public](https://public.tableau.com/app/profile/priyanka.shah1267/vizzes) · [GitHub](https://github.com/pshah580-png)
