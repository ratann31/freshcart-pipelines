from stream.dispatcher import build_message
from stream.driver import validate_message


def test_valid_dispatch_message():
    routing_key, body = build_message(1)
    assert routing_key == "ride.delhi.north.standard"
    assert validate_message(body) == (True, "valid")


def test_every_tenth_message_is_invalid():
    routing_key, body = build_message(10, invalid=True)
    assert routing_key == "ride.invalid.invalid.invalid"
    valid, reason = validate_message(body)
    assert not valid
    assert "missing fields: zone" == reason


def test_malformed_json_is_rejected():
    valid, reason = validate_message(b"{not-json")
    assert not valid
    assert reason.startswith("invalid JSON:")
