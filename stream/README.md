# Part D — RabbitMQ dispatch

## Setup

Install the repository requirements, then start RabbitMQ locally or use an
existing RabbitMQ host:

```powershell
python -m pip install -r requirements.txt
```

Optional environment variables are `RABBITMQ_HOST`, `RABBITMQ_PORT`,
`RABBITMQ_USER`, `RABBITMQ_PASSWORD`, and `RABBITMQ_VHOST`. Credentials are
read at runtime and are never stored in this repository.

The dispatcher declares the durable topic exchange `rapido-dispatch` and
publishes keys in this format:

```text
ride.<city>.<zone>.<type>
```

Every tenth message intentionally omits `zone` and is published with the
`ride.invalid.invalid.invalid` key. Drivers use exclusive private queues,
manual acknowledgements, and `basic_qos(prefetch_count=1)`.

## Run the demonstration

Open four terminals from the repository root:

```powershell
python -m stream.driver --driver-id delhi-north --binding ride.delhi.north.* --duration 120
python -m stream.driver --driver-id mumbai-all --binding ride.mumbai.# --duration 120
python -m stream.driver --driver-id premium --binding ride.*.*.premium --duration 120
python -m stream.dispatcher --duration 120 --interval 2
```

Capture the RabbitMQ management exchange/queue view, dispatcher output, all
three driver outputs, and a discarded invalid message. Valid messages print
`processed` and call `basic_ack`; invalid messages print `discarded` and call
`basic_nack(requeue=False)`.

## Routing-key questions

For `ride.delhi.north.premium`:

| Binding | Matches? | Reason |
|---|---|---|
| `#` | Yes | Matches zero or more words |
| `ride.#` | Yes | Matches every ride key |
| `ride.delhi.#` | Yes | Matches every Delhi ride |
| `ride.*.north.#` | Yes | Matches every northern-zone ride |
| `ride.*.*.premium` | Yes | Matches every premium ride |
| `ride.mumbai.#` | No | Restricts the city to Mumbai |

If a driver crashes before ACK, RabbitMQ redelivers the unacknowledged
message when the connection closes. With `requeue=True`, a rejected message
is placed back on the queue and can loop indefinitely; this implementation
uses `requeue=False` for invalid data so it is discarded.
