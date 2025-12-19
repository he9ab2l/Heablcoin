from __future__ import annotations


from typing import Any, Dict, Optional


_SEND_EMAIL_FN: Optional[Any] = None

_NOTIFY_SWITCH_FN: Optional[Any] = None

_DATA_PROVIDERS: Dict[str, Any] = {}


def set_send_email_fn(fn: Optional[Any]) -> None:

    global _SEND_EMAIL_FN

    _SEND_EMAIL_FN = fn


def get_send_email_fn() -> Optional[Any]:

    return _SEND_EMAIL_FN


def set_notify_switch_fn(fn: Optional[Any]) -> None:

    global _NOTIFY_SWITCH_FN

    _NOTIFY_SWITCH_FN = fn


def get_notify_switch_fn() -> Optional[Any]:

    return _NOTIFY_SWITCH_FN


def set_data_providers(providers: Optional[Dict[str, Any]]) -> None:

    global _DATA_PROVIDERS

    _DATA_PROVIDERS = dict(providers or {})


def get_data_providers() -> Dict[str, Any]:

    return _DATA_PROVIDERS


__all__ = [

    "get_data_providers",

    "get_notify_switch_fn",

    "get_send_email_fn",

    "set_data_providers",

    "set_notify_switch_fn",

    "set_send_email_fn",

]
