"""Consume routed ride requests with explicit ACK/NACK decisions."""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid

from .dispatcher import EXCHANGE

REQUIRED_FIELDS = ("id", "city", "zone", "type", "ts")


def validate_message(body: bytes) -> tuple[bool, str]:
    """Validate a JSON ride message without raising in the callback."""
    try:
        message = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"invalid JSON: {exc}"
    if not isinstance(message, dict):
        return False, "message must be a JSON object"
    missing = [field for field in REQUIRED_FIELDS if not message.get(field)]
    if missing:
        return False, f"missing fields: {', '.join(missing)}"
    return True, "valid"


def connect():
    """Create a RabbitMQ connection from environment configuration."""
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


def consume(driver_id: str, bindings: list[str], duration: float) -> None:
    """Consume for duration seconds from a private, exclusive queue."""
    connection = connect()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    queue_name = f"driver.{driver_id}.{uuid.uuid4().hex[:8]}"
    queue = channel.queue_declare(queue=queue_name, exclusive=True, auto_delete=True).method.queue
    for binding in bindings:
        channel.queue_bind(exchange=EXCHANGE, queue=queue, routing_key=binding)
    channel.basic_qos(prefetch_count=1)
    deadline = time.monotonic() + duration

    def handle_message(ch, method, properties, body):
        valid, reason = validate_message(body)
        if valid:
            print(f"{driver_id} processed {method.routing_key}: {body.decode('utf-8')}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print(f"{driver_id} discarded {reason}: {body!r}", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=queue, on_message_callback=handle_message, auto_ack=False)
    print(f"{driver_id} listening on {bindings}; queue={queue}", flush=True)
    try:
        while time.monotonic() < deadline:
            connection.process_data_events(time_limit=1)
    finally:
        if channel.is_open:
            channel.cancel()
        connection.close()
    print(f"{driver_id} stopped", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Consume Rapido ride requests")
    parser.add_argument("--driver-id", required=True)
    parser.add_argument(
        "--binding",
        action="append",
        dest="bindings",
        help="Topic binding; may be supplied more than once",
    )
    parser.add_argument("--duration", type=float, default=120)
    args = parser.parse_args()
    bindings = args.bindings or ["ride.#"]
    consume(args.driver_id, bindings, args.duration)


if __name__ == "__main__":
    main()

