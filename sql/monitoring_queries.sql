-- DuckDB examples; run from project root after prepare.py.
SELECT step, type, COUNT(*) transaction_count, SUM(amount) transaction_amount,
       SUM(isSAR) simulator_pattern_rows
FROM read_parquet('data/processed/transactions.parquet')
GROUP BY step, type ORDER BY step, type;

SELECT nameOrig AS account, COUNT(*) sent_count, SUM(amount) sent_amount,
       COUNT(DISTINCT nameDest) distinct_recipients
FROM read_parquet('data/processed/transactions.parquet')
GROUP BY nameOrig ORDER BY distinct_recipients DESC LIMIT 100;
