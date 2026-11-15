"""Buffer FreshCart order events and publish them through the existing ELT."""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from .dispatcher import EXCHANGE

LOG = logging.getLogger("bonus_consumer")
ORDER_ROUTING_KEY = "freshcart.orders.#"
SQL_FILES = (
    "10_silver_orders_clean.sql",
    "20_silver_orders_dedup.sql",
    "30_dim_customers_scd2.sql",
    "31_ref_fx_daily.sql",
    "40_gold_fct_orders.sql",
)


def normalize_order(body: bytes) -> tuple[str, dict[str, Any]]:
    """Return a supported source and raw order from a broker message.

    Messages may be an envelope with ``source`` and ``data`` or a direct web
    order object. Mobile messages must identify themselves as ``mobile``.
    """
    try:
        message = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(message, dict):
        raise ValueError("message must be a JSON object")

    source = str(message.get("source", "web")).lower()
    data = message.get("data", message)
    if source not in {"web", "mobile"}:
        raise ValueError("source must be web or mobile")
    if not isinstance(data, dict) or not data:
        raise ValueError("order data must be a non-empty JSON object")
    return source, data


def connect_broker():
    """Create a RabbitMQ connection using runtime environment variables."""
    import pika

    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASSWORD", "guest"),
    )
    parameters = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        credentials=credentials,
        heartbeat=60,
    )
    return pika.BlockingConnection(parameters)


def process_batch(
    orders: list[tuple[str, dict[str, Any]]],
    run_date: date,
    run_id: str,
    landing_dir: Path | None = None,
) -> dict[str, Any]:
    """Write, load, transform, and check one buffered order batch."""
    from freshcart_elt import extract
    from freshcart_elt import snowflake_io
    if not orders:
        raise ValueError("cannot process an empty order batch")

    if landing_dir is not None:
        os.environ["LANDING_DIR"] = str(landing_dir)

    files: dict[str, Path] = {}
    for source in ("web", "mobile"):
        records = [data for item_source, data in orders if item_source == source]
        if records:
            path = extract.write_landing(source, records, run_id, run_date)
            if path is not None:
                files[source] = Path(path)

    if not files:
        raise ValueError("batch did not contain web or mobile orders")

    conn = snowflake_io.connect()
    sql_dir = Path(__file__).parents[1] / "freshcart_elt" / "sql"
    loaded = 0
    try:
        for source, path in files.items():
            loaded += snowflake_io.load_file(
                conn,
                path,
                "bronze.orders_raw",
                f"bonus/{run_date.isoformat()}/{run_id}/{source}",
            )
        variables = {"run_id": run_id, "run_date": run_date.isoformat()}
        for filename in SQL_FILES:
            snowflake_io.run_sql_file(conn, sql_dir / filename, variables)
        duplicate_count = snowflake_io.query_one(
            conn,
            "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM gold.fct_orders",
        )[0]
        if duplicate_count:
            raise RuntimeError(
                f"bonus Gold uniqueness check failed: {duplicate_count} duplicates"
            )
        totals = snowflake_io.query_one(
            conn,
            "SELECT COUNT(*), COALESCE(SUM(amount_inr), 0), "
            "COALESCE(SUM(loyalty_points), 0) FROM gold.fct_orders",
        )
    finally:
        conn.close()

    result = {
        "run_id": run_id,
        "received": len(orders),
        "loaded": loaded,
        "gold_orders": int(totals[0]),
        "gold_revenue": str(totals[1]),
        "gold_points": int(totals[2]),
        "landing_files": [str(path) for path in files.values()],
    }
    LOG.info("bonus batch complete: %s", result)
    return result


def consume_batch(duration: float, run_date: date, run_id: str) -> dict[str, Any]:
    """Collect valid FreshCart messages for ``duration`` seconds and process them."""
    connection = connect_broker()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    queue_name = channel.queue_declare(
        queue=f"bonus.{uuid.uuid4().hex}",
        exclusive=True,
        auto_delete=True,
    ).method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=ORDER_ROUTING_KEY)
    channel.basic_qos(prefetch_count=1)

    orders: list[tuple[str, dict[str, Any]]] = []

    def handle_message(ch, method, properties, body):
        try:
            orders.append(normalize_order(body))
        except ValueError as exc:
            LOG.warning("discarding bonus message: %s", exc)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue_name, on_message_callback=handle_message, auto_ack=False)
    LOG.info("collecting FreshCart orders for %.1f seconds", duration)
    deadline = time.monotonic() + duration
    try:
        while time.monotonic() < deadline:
            connection.process_data_events(time_limit=1)
    finally:
        if channel.is_open:
            channel.cancel()
        connection.close()

    return process_batch(orders, run_date, run_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream FreshCart orders into Gold")
    parser.add_argument("--duration", type=float, default=60)
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_id = args.run_id or f"bonus_{uuid.uuid4().hex[:12]}"
    result = consume_batch(args.duration, date.fromisoformat(args.run_date), run_id)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
