import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT
)

from .core.const import (
    DOMAIN,
    SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    CONF_EXT_EFFECT_SETTINGS,
    CONF_EXT_SENSORS
)
from .core.worker import Worker

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(
        cv.ensure_list,
        [
            vol.Schema({
                vol.Required(CONF_IP_ADDRESS): cv.string,
                vol.Required(CONF_PORT): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default = SCAN_INTERVAL): cv.positive_int,
                vol.Optional(CONF_TIMEOUT, default = DEFAULT_TIMEOUT): cv.positive_int,
                vol.Optional(CONF_EXT_EFFECT_SETTINGS, default = False): cv.boolean,
                vol.Optional(CONF_EXT_SENSORS, default = False): cv.boolean
            })
        ]
    )
}, extra = vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})

    for ledfx in config[DOMAIN]:
        hass.data[DOMAIN][ledfx[CONF_IP_ADDRESS]] = ledfx

        hass.async_create_task(hass.config_entries.flow.async_init(
            DOMAIN, context = {'source': SOURCE_IMPORT}, data = ledfx
        ))

    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    if config_entry.data:
        hass.config_entries.async_update_entry(config_entry, data = {} , options = config_entry.data)

    worker = Worker(hass, config_entry)

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = worker

    if not await worker.async_setup():
        return False

    return True