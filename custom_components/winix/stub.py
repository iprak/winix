"""Winix device stub."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class MyWinixDeviceStub:
    """Winix device information."""

    id: str
    mac: str
    alias: str
    location_code: str
    filter_replace_date: str
    model: str
    sw_version: str
    product_group: str
