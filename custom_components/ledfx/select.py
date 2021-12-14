import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.select import SelectEntity
from .core.common import async_setup_ledfx_entities

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    await async_setup_ledfx_entities(hass, config_entry, async_add_entities, SelectEntity)