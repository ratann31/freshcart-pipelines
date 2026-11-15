# Assignment report evidence

This evidence is extracted from the successful Colab notebooks:

- `D:\DE\Maze_ML_PipeLine_successful.ipynb`
- `D:\DE\freshcart_elt_colab_fixed_successful.ipynb`

## Part B — FreshCart ELT

The successful run loaded six web orders and two mobile orders, giving the
expected eight baseline bronze order rows. The verified downstream results
were:

| Layer/check | Actual result |
|---|---:|
| Silver cleaned rows | 6 |
| Quarantined rows | 2 |
| Deduplicated orders | 4 |
| Gold orders | 4 |
| Gold revenue | 7,785.00 INR |
| Loyalty points | 126 |
| Rejection rate | 25% (2 of 8) |

The gold rows were:

| Order | Tier | Currency | FX rate | Amount INR | Points |
|---|---|---:|---:|---:|---:|
| ORD-1001 | Silver | INR | 1.0000 | 1,250.00 | 12 |
| ORD-1002 | Silver | USD | 83.2000 | 3,536.00 | 35 |
| ORD-1003 | Platinum | INR | 1.0000 | 2,100.00 | 63 |
| ORD-1005 | Gold | INR | 1.0000 | 899.00 | 16 |

The pipeline log showed successful completion of loading, cleansing,
deduplication, SCD2, FX, geography, gold publication, and quality checks.

The notebook was run again and showed 16 bronze rows, proving that another
eight raw records arrived. A final gold-total query must still be captured
after the rerun before claiming the idempotency comparison in the report.

### B3-B5 actual results

The B3-B5 experiment notebook recorded:

- Before validation, ORD-1006 reasons were `bad_email` and `bad_pincode`.
- After validation, ORD-1006 also contained `unsupported_currency`.
- The experiment database contained repeated raw samples from reruns, so the
  post-change query displayed nine copies of ORD-1006 but one distinct order.
- Before B4, the prediction was Silver to Gold, multiplier 1 to 2, points 35
  to 70, and total points 126 to 161.
- Actual B4 results: CUST-02 Gold from 2026-08-15, ORD-1002 amount INR
  3,536.00, 70 points, four gold orders, revenue INR 7,785.00, and total
  loyalty points 161.
- The deliberate B5 run failed as expected because a mock order was present.
  The captured failure also reported the accumulated unsupported-currency,
  no-customer, and quarantine-rate conditions caused by repeated raw samples.
- Cleanup removed the mock order from Bronze, Gold, and Quarantine. The final
  quality checks passed and the final mock-order count was zero.

## Part C — Mage Iris pipeline

Verified output:

- Iris rows loaded: 150.
- Training rows: 120.
- Test rows: 30.
- `max_depth=3` test accuracy: 1.000.
- All block tests shown in the successful run passed.
- `iris_predictions.csv` was created.
- Mage UI tunnel URL was generated.
- `train_model` has parallel downstream blocks `save_results` and
  `evaluate_model` in `metadata.yaml`.

The five-depth experiment table, evaluation metrics/confusion matrix, and
custom-block execution still require dedicated screenshots and output cells.

### C2-C4 actual results

The updated Mage notebook verified:

- `max_depth=3`: test accuracy `1.000`.
- `max_depth=1`: test accuracy `0.633`; the `test_accuracy` quality gate
  failed as intentionally expected.
- The depth-1 run did not create `iris_predictions.csv`.
- The passing depth-3 run created 30 predictions.
- The depth-3 confusion matrix was:

  ```text
  [[10, 0, 0],
   [0,  9, 0],
   [0,  0, 11]]
  ```

- The Mage tunnel URL was generated and the updated metadata connected
  `train_model` to both `save_results` and `evaluate_model`.
- The custom block source contained `@custom` and `@test`, but one pipeline
  run reported that Mage could not load the custom block's decorated function.
  The custom block must be rerun after restarting Mage or rebuilt using a
  supported block type before claiming C4 as complete.

## Screenshot mapping

### Part A

- Repository structure: GitHub repository Code page.
- Git history: `git log --oneline --decorate --graph`.
- Green, red, final green CI: GitHub Actions run pages.

### Part B

- B0: connection test and object listing.
- B1: bronze, silver, quarantine, deduplicated, gold rows, and totals.
- B2: ORD-1003 and ORD-1005 trace.
- B3: ORD-1006 reasons before/after `unsupported_currency`.
- B4: prediction and actual Arjun Gold comparison.
- B5: failing mock-order quality check and final passing check.

### Part C

- C1: completed pipeline graph and run.
- C2: actual `max_depth` 1–5 table and CSV result.
- C3: metadata graph, confusion matrix, metric table, and Mage UI graph.
- C4: custom block code, `@test` pass, and complete pipeline run.

## Not yet evidenced

Part D implementation is now present in `stream/dispatcher.py`,
`stream/driver.py`, and `stream/README.md`. The local payload-validation
checks passed.

The bonus setup is now present in `stream/bonus_consumer.py` and
`stream/bonus_producer.py`. The consumer buffers FreshCart envelopes for a
configurable duration, reuses `write_landing()`, `load_file()`, the existing
transformation SQL, and the Gold `MERGE`, then prints Gold totals. The producer
publishes the eight built-in mock orders for a repeatable smoke test. Unit
tests for envelope normalization and source validation pass.

Still pending are live RabbitMQ execution, driver/dispatcher screenshots,
bonus consumer output, two-run Gold idempotency totals, and final submission
screenshots. No runtime result should be claimed for those sections until
RabbitMQ and Snowflake are executed.
