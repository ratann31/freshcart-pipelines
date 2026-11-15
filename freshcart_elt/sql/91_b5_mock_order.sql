-- B5 experiment: deliberately add a bad order to demonstrate a failing check.
-- Remove this row after capturing the failing quality-check output.
INSERT INTO bronze.orders_raw (source, raw, run_id, extracted_at, src_file, src_row)
SELECT 'web',
       PARSE_JSON('{"order_id":"ORD-MOCK-B5","cust_email":"mock@example.com","cust_name":"Mock","order_date":"2026-09-04","amount":"10","currency":"INR","pincode":"600041","updated_at":"2026-09-04 10:00:00"}'),
       'B5_MOCK',
       CURRENT_TIMESTAMP(),
       'b5_mock_order',
       1
WHERE NOT EXISTS (
  SELECT 1 FROM bronze.orders_raw WHERE raw:order_id::STRING = 'ORD-MOCK-B5'
);
