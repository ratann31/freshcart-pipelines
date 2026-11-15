# From Git to Gold – Data Engineering Assignment

**Roll number:** 23BCS227  
**Repository:** https://github.com/ratann31/freshcart-pipelines  
**Report file:** `23bcs227_data_engineering_assignment.pdf`

## Evidence and status note

This report uses the successful FreshCart and Mage notebook outputs recorded in
`REPORT_EVIDENCE.md`, plus repository code and local tests. It does not invent
RabbitMQ runtime output, screenshots, or bonus totals. Part D runtime and the
lakehouse bonus are implemented or planned in the repository but require a live
broker and execution evidence before submission.

## A. Git and CI/CD (15 marks)

### A1. Repository and commits

The repository is `ratann31/freshcart-pipelines`. It contains FreshCart ELT
code, Mage project material, RabbitMQ code in `stream/`, tests, requirements,
and GitHub Actions configuration. Meaningful milestones include initial setup,
FreshCart ELT, B3–B5 experiments, Mage experiments, quality-check evidence,
and RabbitMQ dispatcher/driver implementation. `git log --oneline` was used
to verify the history.

### A2. Six Git commands

| Command | Purpose |
|---|---|
| `git init` | Creates a local Git repository. |
| `git add train.py` | Stages the named file for the next commit. |
| `git commit -m "message"` | Saves a staged snapshot locally. |
| `git remote add origin URL` | Names the GitHub remote `origin`. |
| `git push -u origin main` | Uploads local `main` and records its upstream. |
| `git pull origin main` | Downloads and merges the remote `main` branch. |

A local commit is not visible to teammates until it is pushed to GitHub.

### A3. Tests and CI

The workflow in `.github/workflows/ci.yml` runs on pushes and pull requests,
installs `requirements.txt`, and runs `pytest`. The deliberate red-run
experiment was produced by making the split assertion false, then the
assertion was restored for the final green run. The focused stream tests also
verify valid payloads, malformed JSON, and the every-tenth invalid message
rule.

## B. FreshCart ELT on Snowflake (30 marks)

### B1. Baseline

Credentials are supplied through Google Colab Secrets and are not stored in
the repository. The verified baseline is:

| Check | Actual result |
|---|---:|
| Bronze raw orders | 8 |
| Silver cleaned rows | 6 |
| Quarantine rows | 2 |
| Deduplicated orders | 4 |
| Gold orders | 4 |
| Gold revenue | INR 7,785.00 |
| Loyalty points | 126 |
| Rejection rate | 25% |

Gold rows were ORD-1001 (Silver, 1,250 INR, 12 points), ORD-1002 (Silver,
3,536 INR after USD conversion, 35 points), ORD-1003 (Platinum, 2,100 INR,
63 points), and ORD-1005 (Gold, 899 INR, 16 points).

### B2. Trace and transformations

The API adapters standardize different source field names into the bronze
schema. ORD-1003 appears twice; the silver deduplication query uses
`ROW_NUMBER()` ordered by the latest `updated_at`, so the mobile record with
the valid amount survives. USD amounts are converted using the reference FX
rate, and points use the amount and the tier multiplier. ORD-1005 receives
Gold points because its order date falls in the Gold SCD2 validity interval,
whereas ORD-1001 joins to the earlier Silver interval.

### B3. Unsupported currency

Before the change, ORD-1006 had `bad_email` and `bad_pincode`. After adding
`unsupported_currency` to the compact validation array, that reason also
appeared. The order remains quarantined; it does not create a new distinct
gold order. Repeated notebook runs accumulated raw samples, so the experiment
displayed nine ORD-1006 copies but one distinct order.

### B4. Arjun Gold event and idempotency

The prediction was: CUST-02 changes from Silver to Gold on 2026-08-15, the
ORD-1002 multiplier changes from 1 to 2, ORD-1002 points change from 35 to 70,
total points change from 126 to 161, and order count/revenue remain unchanged.
The actual results matched:

| Quantity | Predicted | Actual |
|---|---:|---:|
| CUST-02 tier from 2026-08-15 | Gold | Gold |
| ORD-1002 amount INR | 3,536.00 | 3,536.00 |
| ORD-1002 points | 70 | 70 |
| Gold order count | 4 | 4 |
| Gold revenue | 7,785.00 | 7,785.00 |
| Total points | 161 | 161 |

`row_hash` represents the published row content. The Gold `MERGE` matches on
the business key and updates only when the content changes. This makes reruns
idempotent: the same order is not inserted twice. A rerun can increase raw
bronze arrivals, but the deduplication and Gold merge protect the published
order grain.

### B5. Sixth quality check and ETL versus ELT

A mock order was used to make the quality gate fail, producing `PROBLEM`
output. Cleanup removed the mock order from Bronze, Gold, and Quarantine;
Silver and Gold were rebuilt, the final checks passed, and the mock count was
zero. The exact check and its captured failure should be shown in the
submission screenshots.

ELT is suitable here because Snowflake provides scalable storage and SQL
transformation close to the data. Raw records are retained for audit and can
be reprocessed when validation rules change. It also keeps extraction simple
and makes the Silver-to-Gold logic visible. ETL would be preferable when
sensitive data must be transformed before it enters the warehouse or when
the target system has very limited transformation capability.

## C. Mage Iris ML pipeline (20 marks)

The pipeline is `load_iris → prepare_data → train_model`, with parallel
downstream blocks `save_results` and `evaluate_model`. Iris contains 150 rows,
split into 120 training and 30 test rows. The successful depth-3 run achieved
accuracy 1.000 and created 30 predictions.

The intentionally failing depth-1 run achieved accuracy 0.633 and did not
create `iris_predictions.csv`, because the upstream test gate stopped
downstream blocks. The verified depth-3 confusion matrix is:

```text
[[10, 0, 0],
 [ 0, 9, 0],
 [ 0, 0,11]]
```

The updated metadata connects `train_model` to both downstream blocks, and a
Mage tunnel URL was generated. The report must include the actual depth
1–5 table and metric values from the successful notebook output. The custom
block source contains `@custom` and `@test`; one run still reported that Mage
could not discover a decorated function, so C4 is not claimed complete until
the block is rerun after a clean Mage restart.

## D. RabbitMQ food-order streaming (20 marks)

The implementation is in `stream/dispatcher.py` and `stream/driver.py`.
The dispatcher declares the durable topic exchange `rapido-dispatch`, emits
JSON fields `id`, `city`, `zone`, `type`, and `ts`, and sends one invalid
message every tenth message. Drivers use exclusive private queues,
`prefetch_count=1`, manual `basic_ack` for valid messages, and
`basic_nack(requeue=False)` for invalid JSON or missing fields.

For the implemented four-word key format, `#` matches all keys,
`ride.#` matches all ride keys, `ride.delhi.#` matches Delhi rides,
`ride.*.north.#` matches north-zone rides, `ride.*.*.premium` matches premium
rides, and `ride.mumbai.#` matches only Mumbai rides. A crash before ACK
causes RabbitMQ to redeliver the unacknowledged message after connection
closure. `requeue=True` for permanently invalid data can create an infinite
retry loop, so invalid data is discarded.

Local payload-validation tests pass. A live RabbitMQ run with three drivers
and one dispatcher for two minutes, plus screenshots, remains required before
claiming D2/D3 execution results.

## Bonus. Stream into the lakehouse (+10)

The bonus requires a live consumer that buffers FreshCart-style messages for
one minute, writes a landing file through the existing `write_landing()`,
calls `load_file()`, executes the existing transformations, and publishes
through the Gold `MERGE`. It must be run twice and compare Gold totals to prove
idempotency. No live consumer output or before/after totals are present in the
verified evidence, so no bonus result is claimed here.

## E. Report and viva (15 marks)

### Architecture

```text
GitHub repository
      │ push
      ▼
GitHub Actions / pytest ───────────────┐
                                       │
Colab APIs → Landing → Snowflake Bronze│→ Silver → Gold
                                       │       ▲
Mage: load → prepare → train ─────────┘       │
                 ├→ predictions                │
                 └→ evaluation                 │
RabbitMQ dispatcher → topic exchange → drivers ─┘
                                  (bonus consumer to landing)
```

### Reflection

The most important debugging issue was separating notebook execution state
from the intended pipeline logic. Reusing a closed Snowflake connection caused
later SQL cells to fail, while repeated extraction runs also accumulated raw
records. The cause was identified from the exact connection and row-count
errors rather than treating downstream failures as independent bugs. The
solution was to create fresh connections for SQL execution, use an explicit
SQL-file runner, preserve raw data for audit, and rely on deduplication plus
Gold `MERGE` for the published grain. The same evidence-first approach was
used for unsupported-currency validation and the Mage depth-1 quality gate.

## Submission evidence checklist

Attach the actual screenshots for repository structure, Git log and the three
CI states; Snowflake connection, B1/B2/B3/B4/B5 outputs; Mage graph, depth
experiments, metrics, metadata and custom test; RabbitMQ management view,
dispatcher, three drivers and ACK/NACK; and the bonus landing/Bronze/Gold
idempotency comparison. Do not include credentials in screenshots.
