-- B4 experiment: add Arjun's Gold tier event, then rerun the SCD2 and gold steps.
-- The guard makes this setup safe to run more than once.
INSERT INTO bronze.customers_raw (source, raw, run_id, extracted_at, src_file, src_row)
SELECT 'crm',
       PARSE_JSON('{"cust_id":"CUST-02","email":"arjun.k@yahoo.in","tier":"Gold","effective_from":"2026-08-15"}'),
       'B4_ARJUN_GOLD',
       CURRENT_TIMESTAMP(),
       'b4_arjun_gold',
       1
WHERE NOT EXISTS (
  SELECT 1
  FROM bronze.customers_raw
  WHERE raw:cust_id::STRING = 'CUST-02'
    AND raw:effective_from::DATE = '2026-08-15'::DATE
);
