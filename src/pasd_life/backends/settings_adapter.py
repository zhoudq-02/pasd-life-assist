"""Small value object decoupling the hardware adapter from Settings."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterSettings:
    can_interface: str
    can_bitrate: int
    serial_device: str
    adapter: str = "sdk"

    @classmethod
    def from_settings(cls, s) -> "AdapterSettings":
        return cls(
            can_interface=s.can_interface,
            can_bitrate=s.can_bitrate,
            serial_device=s.serial_device,
            adapter=s.adapter,
        )
