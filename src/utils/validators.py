import re

_SYMBOL_REGEX = re.compile(r"^[A-Z][A-Z0-9\.-]{0,9}$")


def is_valid_symbol(symbol: str) -> bool:
    """Return True if *symbol* looks like a valid ticker."""

    return bool(_SYMBOL_REGEX.fullmatch(symbol.upper()))
