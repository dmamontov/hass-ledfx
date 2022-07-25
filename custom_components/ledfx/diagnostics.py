"""LedFx diagnostic."""

from __future__ import annotations

from typing import Final

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .updater import async_get_updater

TO_REDACT: Final = {
    CONF_PASSWORD,
    CONF_USERNAME,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""

    _data: dict = {"config_entry": async_redact_data(config_entry.as_dict(), TO_REDACT)}

    if _updater := async_get_updater(hass, config_entry.entry_id):
        if hasattr(_updater, "data"):
            _data["data"] = async_redact_data(_updater.data, TO_REDACT)

        if len(_updater.client.diagnostics) > 0:
            _data["requests"] = async_redact_data(
                _updater.client.diagnostics, TO_REDACT
            )

        if hasattr(_updater, "buttons") and _updater.buttons:
            _data["buttons"] = list(_updater.buttons.keys())

        if hasattr(_updater, "devices") and _updater.devices:
            _data["devices"] = list(_updater.devices.keys())

        if hasattr(_updater, "numbers") and _updater.numbers:
            _data["numbers"] = list(_updater.numbers.keys())

        if hasattr(_updater, "selects") and _updater.selects:
            _data["selects"] = list(_updater.selects.keys())

        if hasattr(_updater, "sensors") and _updater.sensors:
            _data["sensors"] = list(_updater.sensors.keys())

        if hasattr(_updater, "switches") and _updater.switches:
            _data["switches"] = list(_updater.switches.keys())

    return _data
