# FreshCart ELT

This implementation is adapted from the supplied FreshCart Colab notebook:

```text
extract.py -> landing/*.json.gz -> Snowflake bronze
                                  -> silver validation/cleaning
                                  -> SCD2, FX, geography enrichment
                                  -> gold.fct_orders
```

## Colab setup

Install the FreshCart dependencies in a Colab cell:

```python
%pip install -q -r /content/freshcart_elt/requirements.txt
```

Add these values in Colab Secrets (the key icon), enabling notebook access for
each secret:

```text
SNOWFLAKE_ACCOUNT=YLGAZKY-WR98502
SNOWFLAKE_USER=RATANN31
SNOWFLAKE_PASSWORD=<your password, never put it in a file>
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=FRESHCART_WH
SNOWFLAKE_DATABASE=FRESHCART
```

The notebook or shell environment must read those values with `os.getenv`;
never print them. Run the baseline only after the connection test succeeds:

```powershell
python run_pipeline.py --setup --mock --run-date 2026-09-04
python run_pipeline.py --mock --run-date 2026-09-04
```

Expected baseline verification from the supplied mock data:

| Check | Expected |
|---|---:|
| Bronze order rows | 8 |
| Clean silver rows | 6 |
| Quarantined rows | 2 |
| Deduplicated orders | 4 |
| Gold orders | 4 |
| Revenue (`SUM(amount_inr)`) | 7,785.00 |
| Loyalty points | 126 |
| Rejection rate | 25% |

The quarantine-rate check is intentionally a warning for this assignment
sample. The unsupported-currency validation adds `unsupported_currency` to
ORD-1006 alongside its existing invalid-email and invalid-pincode reasons.

## Colab screenshot checkpoints

Add a short Markdown cell with the matching heading before each query below.
Run the query, keep the result visible, and capture the screenshot immediately.
Do not include the Secrets panel or any credential value in a screenshot.

### Screenshot B0 — connection and objects

```sql
SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
SHOW DATABASES LIKE 'FRESHCART';
SHOW SCHEMAS IN DATABASE FRESHCART;
```

### Screenshot B1 — baseline row counts

```sql
SELECT COUNT(*) AS bronze_orders FROM bronze.orders_raw;
SELECT COUNT(*) AS silver_clean FROM silver.orders_clean;
SELECT COUNT(*) AS quarantined FROM quarantine.orders;
SELECT COUNT(*) AS deduplicated FROM silver.orders_dedup;
```

### Screenshot B1 — gold totals

```sql
SELECT order_id, order_date, tier, amount, currency, fx_rate, amount_inr,
       loyalty_points, city, region
FROM gold.fct_orders
ORDER BY order_id;

SELECT COUNT(*) AS orders,
       SUM(amount_inr) AS revenue_inr,
       SUM(loyalty_points) AS loyalty_points
FROM gold.fct_orders;
```

### Screenshot B2 — manual order traces

```sql
SELECT * FROM silver.orders_checked WHERE order_id IN ('ORD-1003', 'ORD-1005');
SELECT * FROM silver.orders_dedup WHERE order_id IN ('ORD-1003', 'ORD-1005');
SELECT * FROM gold.fct_orders WHERE order_id IN ('ORD-1003', 'ORD-1005');
```

### Screenshot B3 — unsupported currency

Capture ORD-1006 from `silver.orders_checked` before and after the
`unsupported_currency` change:

```sql
SELECT order_id, currency, reasons
FROM silver.orders_checked
WHERE order_id = 'ORD-1006';
```

### Screenshot B4 — prediction and actual comparison

Before running `sql/90_b4_add_arjun_gold.sql`, write the five expected values
in a Markdown cell. After rerunning the SCD2 and gold statements, query:

```sql
SELECT * FROM dim.customers_scd2
WHERE cust_id = 'CUST-02'
ORDER BY valid_from;

SELECT order_id, tier, multiplier, amount_inr, loyalty_points
FROM gold.fct_orders
WHERE email = 'arjun.k@yahoo.in';
```

### Screenshot B5 — quality check failure and cleanup

Run `sql/91_b5_mock_order.sql`, rerun the transformations, and capture the
`no mock orders in production` failure. Then remove the mock row and rerun:

```sql
DELETE FROM bronze.orders_raw
WHERE raw:order_id::STRING = 'ORD-MOCK-B5';
```

## Assignment experiments

1. Capture the baseline table queries and the ORD-1003/ORD-1005 trace.
2. Run the validation change and compare ORD-1006 reasons.
3. Execute `sql/90_b4_add_arjun_gold.sql`, then rerun the SCD2 and gold SQL.
   Record predictions before execution and compare all five requested values.
4. Execute `sql/91_b5_mock_order.sql`, rerun the transformations, and capture
   the failing `no mock orders in production` check. Remove the mock row before
   the final run.

`row_hash` lets the gold `MERGE` update only changed orders. Matching unchanged
rows are ignored, so rerunning the same batch is idempotent.
