"""String utility helpers."""


def sanitize_value(value: str | None) -> str | None:
    """Strip whitespace and surrounding quotes from a value.

    Args:
        value: The raw string value to sanitize.

    Returns:
        The sanitized string, or None if input was None.
    """
    if value is None:
        return None
    sanitized = value.strip()
    for quote in ('"', "'"):
        if (
            sanitized.startswith(quote)
            and sanitized.endswith(quote)
            and len(sanitized) >= 2
        ):
            return sanitized[1:-1]
    return sanitized
