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
