"""LedFx custom integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant

from .const import (
    DEFAULT_CALL_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLEEP,
    DEFAULT_TIMEOUT,
    DOMAIN,
    OPTION_IS_FROM_FLOW,
    PLATFORMS,
    UPDATE_LISTENER,
    UPDATER,
)
from .helper import build_auth, get_config_value
from .updater import LedFxUpdater

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up entry configured via user interface.

    :param hass: HomeAssistant: Home Assistant object
    :param entry: ConfigEntry: Config Entry object
    :return bool: Is success
    """

    is_new: bool = get_config_value(entry, OPTION_IS_FROM_FLOW, False)

    if is_new:
        hass.config_entries.async_update_entry(entry, data=entry.data, options={})

    _updater: LedFxUpdater = LedFxUpdater(
        hass,
        get_config_value(entry, CONF_IP_ADDRESS),
        get_config_value(entry, CONF_PORT),
        build_auth(
            get_config_value(entry, CONF_USERNAME),
            get_config_value(entry, CONF_PASSWORD),
        ),
        get_config_value(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        get_config_value(entry, CONF_TIMEOUT, DEFAULT_TIMEOUT),
    )

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {UPDATER: _updater}

    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = entry.add_update_listener(
        async_update_options
    )

    async def async_start(with_sleep: bool = False) -> None:
        """Async start.

        :param with_sleep: bool
        """

        await _updater.async_config_entry_first_refresh()

        if with_sleep:
            await asyncio.sleep(DEFAULT_SLEEP)

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if is_new:
        await async_start()
        await asyncio.sleep(DEFAULT_SLEEP)
    else:
        hass.loop.call_later(
            DEFAULT_CALL_DELAY,
            lambda: hass.async_create_task(async_start(True)),
        )

    async def async_stop(event: Event) -> None:
        """Async stop"""

        await _updater.async_stop()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_stop)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options for entry that was configured via user interface.

    :param hass: HomeAssistant: Home Assistant object
    :param entry: ConfigEntry: Config Entry object
    """

    if entry.entry_id not in hass.data[DOMAIN]:
        return

    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove entry configured via user interface.

    :param hass: HomeAssistant: Home Assistant object
    :param entry: ConfigEntry: Config Entry object
    :return bool: Is success
    """

    if is_unload := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        _updater: LedFxUpdater = hass.data[DOMAIN][entry.entry_id][UPDATER]
        await _updater.async_stop()

        _update_listener: CALLBACK_TYPE = hass.data[DOMAIN][entry.entry_id][
            UPDATE_LISTENER
        ]
        _update_listener()

        hass.data[DOMAIN].pop(entry.entry_id)

    return is_unload
