"""Winix device stub."""

import dataclasses


@dataclasses.dataclass
class MyWinixDeviceStub:
    """Winix device information."""

    id: str
    """Device ID"""
    mac: str
    """Device MAC address"""
    alias: str
    """Device alias"""
    location_code: str
    """Device location code"""
    filter_replace_date: str
    """Filter replacement date"""
    model: str
    """Model name"""
    model_id: str
    """Model ID"""
    sw_version: str
    """Software version"""
    product_group: str
    """Product group"""
