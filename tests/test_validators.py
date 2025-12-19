import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)
from utils.validators import (


    parse_price,
    validate_price_condition,
    is_valid_wallet_address,
    normalize_symbol,
)


def test_parse_price():
    assert parse_price("123.45") == 123.45
    assert parse_price(10) == 10.0
    assert parse_price("12_345") == 12345.0
    try:
        parse_price("-1", min_value=0)
    except ValueError:
        return
    raise AssertionError("negative price should fail")


def test_validate_condition():
    assert validate_price_condition("price < 50000") == 50000.0
    try:
        validate_price_condition("volume > 10")
    except ValueError:
        return
    raise AssertionError("invalid condition must raise")


def test_wallet_addresses():
    assert is_valid_wallet_address("0x" + "a" * 40)
    assert not is_valid_wallet_address("0x123")
    assert is_valid_wallet_address("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080", "btc")


def test_normalize_symbol():
    assert normalize_symbol("eth\\usdt") == "ETH/USDT"
