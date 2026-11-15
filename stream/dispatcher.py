"""Publish ride requests to the Rapido topic exchange."""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from itertools import count

EXCHANGE = "rapido-dispatch"
CITIES = ("delhi", "mumbai", "bengaluru")
ZONES = ("north", "south", "east", "west")
RIDE_TYPES = ("standard", "premium")


def build_message(sequence: int, invalid: bool = False) -> tuple[str, bytes]:
    """Return a routing key and JSON body for one dispatch event."""
    city = CITIES[(sequence - 1) % len(CITIES)]
    zone = ZONES[(sequence - 1) % len(ZONES)]
    ride_type = RIDE_TYPES[(sequence - 1) % len(RIDE_TYPES)]
    routing_key = f"ride.{city}.{zone}.{ride_type}"
    message = {
        "id": f"RIDE-{sequence:05d}",
        "city": city,
        "zone": zone,
        "type": ride_type,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    if invalid:
        message.pop("zone")
        routing_key = "ride.invalid.invalid.invalid"
    return routing_key, json.dumps(message).encode("utf-8")


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


def publish(duration: float, interval: float) -> None:
    """Publish one event every interval seconds for duration seconds."""
    import pika

    connection = connect()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    deadline = time.monotonic() + duration
    sequence = count(1)
    sent = 0
    try:
        while time.monotonic() < deadline:
            number = next(sequence)
            invalid = number % 10 == 0
            routing_key, body = build_message(number, invalid=invalid)
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )
            sent += 1
            print(f"published {routing_key}: {body.decode('utf-8')}", flush=True)
            time.sleep(interval)
    finally:
        connection.close()
    print(f"dispatcher stopped; published={sent}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish Rapido ride requests")
    parser.add_argument("--duration", type=float, default=120)
    parser.add_argument("--interval", type=float, default=2)
    args = parser.parse_args()
    publish(args.duration, args.interval)


if __name__ == "__main__":
    main()

