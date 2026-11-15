"""Small, testable data-preparation helper used by the CI example."""

from collections.abc import Iterable


def prepare_data(values: Iterable[object]) -> list[str]:
    """Normalize non-empty values into trimmed strings.

    The helper is deliberately small so the CI example focuses on the
    add/commit/push workflow rather than framework-specific behavior.
    """
    result = [str(value).strip() for value in values]
    return [value for value in result if value]

