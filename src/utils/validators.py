from __future__ import annotations


import re

from typing import Union


Numeric = Union[str, int, float]


_PRICE_PATTERN = re.compile(r"^\d+(\.\d+)?$")

_EVM_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")

_BTC_ADDRESS_PATTERN = re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$")

_CONDITION_PATTERN = re.compile(r"^\s*price\s*(<=|>=|<|>)\s*(-?\d+(\.\d+)?)\s*$", re.IGNORECASE)


def parse_price(value: Numeric, min_value: float = 0.0) -> float:

    if isinstance(value, (int, float)):

        price = float(value)

    elif isinstance(value, str):

        candidate = value.strip().replace(",", "").replace("_", "")

        if not candidate or not _PRICE_PATTERN.match(candidate):

            raise ValueError(f"Invalid price value: {value}")

        price = float(candidate)

    else:

        raise ValueError(f"Unsupported price type: {type(value)}")


    if price < min_value:

        raise ValueError(f"Price must be >= {min_value}, got {price}")

    return price


def validate_price_condition(condition: str) -> float:

    if not condition:

        raise ValueError("Condition is required")

    match = _CONDITION_PATTERN.match(condition)

    if not match:

        raise ValueError("Condition must be like: price < 50000")

    return float(match.group(2))


def is_valid_wallet_address(address: str, chain: str = "EVM") -> bool:

    if not address:

        return False

    chain = (chain or "EVM").upper()

    if chain == "BTC":

        return bool(_BTC_ADDRESS_PATTERN.match(address))

    return bool(_EVM_ADDRESS_PATTERN.match(address))


def normalize_symbol(symbol: str) -> str:

    if not symbol:

        return ""

    return symbol.replace("\\", "/").upper()


__all__ = [

    "parse_price",

    "validate_price_condition",

    "is_valid_wallet_address",

    "normalize_symbol",

]
