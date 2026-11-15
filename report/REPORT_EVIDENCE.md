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

Parts D, the bonus RabbitMQ-to-Snowflake integration, and the final PDF
assembly are still pending. No result or screenshot should be claimed for
those sections until they are executed.
