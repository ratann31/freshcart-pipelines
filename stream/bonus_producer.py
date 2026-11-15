"""Publish the built-in FreshCart mock orders for a bonus smoke test."""

from __future__ import annotations

import argparse
import json

from freshcart_elt import mock_data

from .bonus_consumer import ORDER_ROUTING_KEY
from .dispatcher import connect, EXCHANGE


def publish_mock_orders() -> int:
    import pika

    connection = connect()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    published = 0
    try:
        for source, records in (("web", mock_data.WEB_ORDERS), ("mobile", mock_data.MOBILE_ORDERS)):
            for record in records:
                body = json.dumps({"source": source, "data": record}).encode("utf-8")
                channel.basic_publish(
                    exchange=EXCHANGE,
                    routing_key="freshcart.orders." + source,
                    body=body,
                    properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
                )
                published += 1
                print(f"published {source} order {record.get('order_id', record.get('orderId'))}", flush=True)
    finally:
        connection.close()
    return published


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish FreshCart mock orders")
    parser.parse_args()
    print(f"published={publish_mock_orders()}", flush=True)
