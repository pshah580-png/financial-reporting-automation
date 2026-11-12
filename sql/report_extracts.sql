-- ============================================================
-- Financial Reporting Automation — Extract / aggregation queries
-- Data: SYNTHETIC demo data — created for portfolio demonstration;
--       not employer data. Fictional accounts and tickers only.
-- Tables (loaded by python/generate_reports.py):
--   trades(trade_id, trade_date, account_id, ticker, side,
--          quantity, price, settlement_date, notional)
--   positions(as_of_date, account_id, ticker, quantity,
--             market_price, market_value)
--   report_schedule(report_name, frequency, audience, format)
-- Dialect: SQLite / standard SQL.
-- ============================================================

-- 1) DAILY TRADE SUMMARY — volume and notional per day
SELECT
    trade_date,
    COUNT(*)                          AS trade_count,
    SUM(CASE WHEN side = 'BUY'  THEN 1 ELSE 0 END) AS buy_count,
    SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
    SUM(quantity)                     AS total_quantity,
    ROUND(SUM(notional), 2)           AS total_notional
FROM trades
GROUP BY trade_date
ORDER BY trade_date;

-- 2) ACCOUNT ACTIVITY — per account, per day (client-reporting view)
SELECT
    trade_date, account_id,
    COUNT(*)                AS trade_count,
    ROUND(SUM(notional), 2) AS total_notional
FROM trades
GROUP BY trade_date, account_id
ORDER BY trade_date, account_id;

-- 3) POSITIONS SNAPSHOT — holdings value per account (month-end)
SELECT
    account_id,
    COUNT(DISTINCT ticker)       AS holdings_count,
    ROUND(SUM(market_value), 2)  AS total_market_value
FROM positions
GROUP BY account_id
ORDER BY total_market_value DESC;

-- 4) CONTROL TOTAL — report figures must tie back to the raw trades.
-- If this differs from the sum of the daily summary, the run is flagged
-- in the audit log instead of being released silently.
SELECT ROUND(SUM(notional), 2) AS control_total_notional, COUNT(*) AS control_trade_count
FROM trades;
