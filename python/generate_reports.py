#!/usr/bin/env python3
"""
Financial Reporting Automation — runnable report generator (stdlib only).

IMPORTANT: All data in ../data is SYNTHETIC demo data — created for
portfolio demonstration; not employer data. Accounts/tickers are fictional.
Effort figures in the summary are a DEMO SCENARIO for illustration,
not measured results from a real employer.

What it does:
  1. Loads synthetic trades / positions / report schedule into SQLite.
  2. Generates the scheduled reports (daily trade summary, account
     activity, positions snapshot) as CSVs in ../output/.
  3. Writes a plain-English text summary of the latest day.
  4. Verifies a control total (report totals must tie to raw trades)
     and appends an audit-log line: run time, rows read, files written,
     control status. A failed control is logged as FAILED, not hidden.

Run:  python python/generate_reports.py   (from the project folder)
Schedule it (concept): cron / Task Scheduler / any orchestrator, e.g.
  30 6 * * 1-5  python generate_reports.py   # 06:30, business days
"""
import csv, os, sqlite3, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA, OUT = os.path.join(ROOT, "data"), os.path.join(ROOT, "output")

def load_csv(con, table, filename):
    with open(os.path.join(DATA, filename), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    con.execute(f"CREATE TABLE {table} ({', '.join(c + ' TEXT' for c in cols)})")
    con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(cols))})",
                    [tuple(r[c] for c in cols) for r in rows])
    return len(rows)

def write_csv(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    return name, len(rows)

def main():
    os.makedirs(OUT, exist_ok=True)
    started = datetime.now(timezone.utc)
    con = sqlite3.connect(":memory:")
    n_trades = load_csv(con, "trades", "trades.csv")
    n_pos = load_csv(con, "positions", "positions.csv")
    load_csv(con, "report_schedule", "report_schedule.csv")
    print(f"Loaded: trades={n_trades}, positions={n_pos}")

    written = []
    daily = con.execute("""
        SELECT trade_date, COUNT(*),
               SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END),
               SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END),
               SUM(CAST(quantity AS INTEGER)),
               ROUND(SUM(CAST(notional AS REAL)), 2)
        FROM trades GROUP BY trade_date ORDER BY trade_date""").fetchall()
    written.append(write_csv("daily_trade_summary.csv",
        ["trade_date", "trade_count", "buy_count", "sell_count",
         "total_quantity", "total_notional"], daily))

    activity = con.execute("""
        SELECT trade_date, account_id, COUNT(*),
               ROUND(SUM(CAST(notional AS REAL)), 2)
        FROM trades GROUP BY trade_date, account_id
        ORDER BY trade_date, account_id""").fetchall()
    written.append(write_csv("account_activity_summary.csv",
        ["trade_date", "account_id", "trade_count", "total_notional"], activity))

    snapshot = con.execute("""
        SELECT account_id, COUNT(DISTINCT ticker),
               ROUND(SUM(CAST(market_value AS REAL)), 2)
        FROM positions GROUP BY account_id
        ORDER BY SUM(CAST(market_value AS REAL)) DESC""").fetchall()
    written.append(write_csv("positions_snapshot.csv",
        ["account_id", "holdings_count", "total_market_value"], snapshot))

    # Control check: report totals must tie exactly to the raw trades.
    ctrl_total, ctrl_count = con.execute(
        "SELECT ROUND(SUM(CAST(notional AS REAL)),2), COUNT(*) FROM trades"
    ).fetchone()
    report_total = round(sum(r[5] for r in daily), 2)
    status = "SUCCESS" if (report_total == ctrl_total
                           and sum(r[1] for r in daily) == ctrl_count) else "FAILED"

    latest = daily[-1]
    with open(os.path.join(OUT, "latest_day_summary.txt"), "w") as f:
        f.write("Financial Reporting Automation - Latest Day Summary\n")
        f.write("Data: SYNTHETIC demo data - not employer data.\n\n")
        f.write(f"Latest trade date : {latest[0]}\n")
        f.write(f"Trades            : {latest[1]} "
                f"({latest[2]} buys / {latest[3]} sells)\n")
        f.write(f"Total quantity    : {latest[4]}\n")
        f.write(f"Total notional    : ${latest[5]:,.2f}\n")
        f.write(f"Control total     : ${ctrl_total:,.2f} across "
                f"{ctrl_count} trades - {status}\n\n")
        f.write("Demo-scenario effort framing (illustrative, synthetic):\n")
        f.write("  Manual process : ~45 min/day of copy, format, check, send\n")
        f.write("  Automated      : ~2 min/day to review the audit log\n")
        f.write("  Framing only - not a measured employer result.\n")
    written.append(("latest_day_summary.txt", 1))

    log_path = os.path.join(OUT, "audit_log.csv")
    new_log = not os.path.exists(log_path)
    with open(log_path, "a", newline="") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(["run_timestamp_utc", "trades_read", "positions_read",
                        "files_written", "control_total", "status", "data_note"])
        w.writerow([started.strftime("%Y-%m-%dT%H:%M:%SZ"), n_trades, n_pos,
                    "; ".join(n for n, _ in written), ctrl_total, status,
                    "Synthetic demo data"])
    print(f"Files written: {written}")
    print(f"Control total ${ctrl_total:,.2f} - {status} (see output/audit_log.csv)")
    return 0 if status == "SUCCESS" else 1

if __name__ == "__main__":
    sys.exit(main())
