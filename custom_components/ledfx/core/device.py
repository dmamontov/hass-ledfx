import logging

from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT

import homeassistant.helpers.device_registry as dr

from .ledfx import LedFx
from .const import DOMAIN, DEFAULT_MANUFACTURER
from .effects import Effects, Effect

_LOGGER = logging.getLogger(__name__)

class Device(object):
    def __init__(
            self,
            hass: HomeAssistant,
            config_entry: ConfigEntry,
            api: LedFx,
            id: str,
            version: str,
            name: Optional[str] = DOMAIN,
            model: Optional[str] = None,
            effects: Optional[Effects] = None
    ) -> None:
        self.hass = hass
        self.config_entry = config_entry

        self._id = id
        self._api = api
        self._name = name
        self._version = version
        self._model = model
        self._effects = effects
        self._is_available = False

        self._entities = {}
        self._entities_data = {}

        self._effect_properties = {}

        self._last_effect = effects.first if effects is not None else None

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> Optional[str]:
        return self._model

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def api(self) -> str:
        return self._api

    @property
    def effects(self) -> Effects:
        return self._effects

    @property
    def last_effect(self) -> Optional[Effect]:
        return self._last_effect

    @property
    def host(self) -> str:
        return "{}:{}".format(
            self.config_entry.options[CONF_IP_ADDRESS],
            self.config_entry.options[CONF_PORT]
        )

    @property
    def identifiers(self):
        return {(DOMAIN, "{}-{}".format(self.host, self._id))}

    @property
    def url(self) -> str:
        return "http://{}/dashboard".format(self.host) if self._id == DOMAIN else \
            "http://{}/devices/{}".format(self.host, self._id)

    @property
    def entities(self) -> dict:
        return self._entities

    async def async_update_available(self, is_available: bool) -> None:
        self._is_available = is_available

    async def async_update(self) -> None:
        (await dr.async_get_registry(self.hass)).async_get_or_create(
            config_entry_id = self.config_entry.entry_id,
            identifiers = self.identifiers,
            name = self._name,
            manufacturer = DEFAULT_MANUFACTURER,
            model = self._model,
            sw_version = self._version,
            configuration_url = self.url,
        )

    async def async_append_entity(self, entity: Entity, options: dict = {}) -> None:
        if entity.id not in self._entities:
            self._entities[entity.id] = entity

        if entity.id in self._entities_data and "support_effects" in options:
            options["support_effects"] = list(set(
                self._entities_data[entity.id]["support_effects"] + options["support_effects"]
            ))

        self._entities_data[entity.id] = options

    async def set_effect(self, effect: Effect) -> None:
        self._last_effect = effect

    def get_entity_data(self, id: str) -> Optional[dict]:
        if id not in self._entities_data:
            return None

        return self._entities_data[id]

    def update_entity_data(self, id: str, code: str, value) -> None:
        self._entities_data[id][code] = value

    def get_entity(self, id: str) -> Optional[dict]:
        if id not in self._entities:
            return None

        return self._entities[id]

    def add_effect_property(self, effect: str, code: str, value, is_update: bool = False) -> None:
        if effect not in self._effect_properties:
            self._effect_properties[effect] = {"active": True}

        if not code in self._effect_properties[effect] or is_update:
            self._effect_properties[effect][code] = value

    def get_effect_property(self, effect: str) -> dict:
        return self._effect_properties[effect] if effect in self._effect_properties else {}

class Devices(object):
    def __init__(self) -> None:
        self._devices = {}

    @property
    def list(self) -> dict:
        return self._devices

    async def async_append(self, device: Device) -> None:
        self._devices[device.id] = device

    def get(self, id: str) -> Optional[Device]:
        return self._devices[id] if id in self._devices else None

    def has(self, id: str) -> bool:
        return id in self._devices
