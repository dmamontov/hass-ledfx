import logging

from typing import Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.light import (
    LightEntity,
    SUPPORT_EFFECT,
    ATTR_EFFECT,
    SUPPORT_BRIGHTNESS,
    ATTR_BRIGHTNESS
)
from homeassistant.components.number import NumberEntity
from homeassistant.components.number.const import DEFAULT_MAX_VALUE, DEFAULT_MIN_VALUE
from homeassistant.components.select import SelectEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.const import ENTITY_CATEGORY_CONFIG, ENTITY_CATEGORY_DIAGNOSTIC

from .const import DATA_UPDATED, DOMAIN, ICONS
from .device import Device

_LOGGER = logging.getLogger(__name__)

async def async_setup_ledfx_entities(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        type
) -> None:
    worker = hass.data[DOMAIN][config_entry.entry_id]

    @callback
    def update_devices() -> None:
        if len(worker.devices.list) == 0:
            return

        new_devices = []
        for id in worker.devices.list:
            device = worker.devices.list[id]
            for entity in device.entities:
                entity = device.entities[entity]
                if not isinstance(entity, type) or not entity.is_new:
                    continue

                entity.added()

                _LOGGER.debug("Debug LedFx update {} {} {}".format(type, id, entity.id))

                new_devices.append(entity)

        if len(new_devices) > 0:
            async_add_entities(new_devices)

    async_dispatcher_connect(
        hass, DATA_UPDATED, update_devices
    )

class LedFxEntity(Entity):
    def __init__(
            self,
            device: Device,
            id: str,
            name: str
    ) -> None:
        self._device = device
        self._id = id
        self._name = name
        self._is_new = True
        self._is_available = True

        self.unsub_update = None

    @property
    def is_new(self) -> bool:
        return self._is_new

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return "{}_{}_{}".format(self._device.config_entry.entry_id, self._device.id, self._id)

    @property
    def available(self) -> bool:
        return self._device.is_available and self._is_available

    @property
    def device_info(self) -> dict:
        return {"identifiers": self._device.identifiers}

    @property
    def icon(self) -> Optional[str]:
        return ICONS[self._id] if self._id in ICONS else None

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self) -> None:
        self.unsub_update = async_dispatcher_connect(
            self._device.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @callback
    def _schedule_immediate_update(self) -> None:
        self.async_schedule_update_ha_state(True)

    async def will_remove_from_hass(self) -> None:
        if self.unsub_update:
            self.unsub_update()

        self.unsub_update = None

    def added(self) -> None:
        self._is_new = False

    def enable(self) -> None:
        self._is_available = True

    def disable(self) -> None:
        self._is_available = False

    async def async_send(self, value) -> None:
        if not self.available:
            return

        try:
            await self._device.api.effect(
                self._device.id,
                self._device.last_effect.code,
                {"active": True, self._id: value}
            )
        except Exception as e:
            _LOGGER.error("ERROR LedFx send command %r", e)

class LedFxSensor(SensorEntity, LedFxEntity):
    @property
    def entity_category(self) -> str:
        return ENTITY_CATEGORY_DIAGNOSTIC

    @property
    def native_value(self) -> Optional[str]:
        return self._device.get_entity_data(self._id)["value"]

class LedFxBinarySensor(BinarySensorEntity, LedFxEntity):
    @property
    def entity_category(self) -> str:
        return ENTITY_CATEGORY_DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return self._device.get_entity_data(self._id)["is_on"]

class LedFxSwitch(SwitchEntity, LedFxEntity):
    @property
    def is_on(self) -> bool:
        return self._device.get_entity_data(self._id)["is_on"]

class LedFxSelect(SelectEntity, LedFxEntity):
    @property
    def entity_category(self) -> str:
        return ENTITY_CATEGORY_CONFIG

    @property
    def current_option(self) -> Optional[str]:
        return self._device.get_entity_data(self._id)["current_option"]

    @property
    def options(self) -> list:
        return self._device.get_entity_data(self._id)["options"]

class LedFxLight(LightEntity, LedFxEntity):
    @property
    def icon(self) -> Optional[str]:
        return self._device.get_entity_data(self._id)["icon"]

    @property
    def is_on(self) -> bool:
        return self._device.get_entity_data(self._id)["is_on"]

    @property
    def brightness(self) -> float:
        brightness = self._device.get_entity_data(self._id)["brightness"]

        return 255 if brightness > 255 else brightness

    @property
    def effect(self) -> Optional[str]:
        return self._device.get_entity_data(self._id)["effect"] if self.is_on else None

    @property
    def effect_list(self) -> list:
        return self._device.effects.list

    @property
    def supported_features(self) -> int:
        supports = 0

        if len(self.effect_list) > 0:
            supports |= SUPPORT_EFFECT
        if self.is_on and self._device.last_effect is not None \
                and self._device.last_effect.is_brightness:
            supports |= SUPPORT_BRIGHTNESS

        return supports

    async def async_turn_on(self, **kwargs) -> None:
        is_preset = False
        effect = None

        if ATTR_EFFECT in kwargs and (self.supported_features & SUPPORT_EFFECT) \
                and kwargs[ATTR_EFFECT] in self.effect_list:
            effect = self._device.effects.get(kwargs[ATTR_EFFECT])

            if effect.is_preset:
                await self._device.set_effect(effect.parent)
                is_preset = True
            else:
                await self._device.set_effect(effect)

        try:
            if is_preset:
                await self._device.api.preset(self._id, effect.category, self._device.last_effect.code, effect.code)
            else:
                await self._device.api.on(self._id, self._device.last_effect.code)

            if ATTR_BRIGHTNESS in kwargs and self._device.last_effect.is_brightness:
                brightness = float(kwargs[ATTR_BRIGHTNESS] / 100 / 2.55)

                await self._device.api.effect(
                    self._id,
                    self._device.last_effect.code,
                    {"active": True, "brightness": 1.0 if brightness > 1.0 else brightness}
                )

            self._device.update_entity_data(self._id, "is_on", True)
        except Exception as e:
            _LOGGER.error("ERROR turn_on LedFx %r", e)

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self._device.api.off(self._id)
            self._device.update_entity_data(self._id, "is_on", False)
        except Exception as e:
            _LOGGER.error("ERROR turn_off LedFx %r", e)

class Scene(LedFxSwitch):
    @property
    def icon(self) -> Optional[str]:
        return "mdi:image"

    @property
    def is_on(self) -> bool:
        return False

    async def async_turn_on(self, **kwargs) -> None:
        if not self.available:
            return

        try:
            await self._device.api.run_scene(self.id)
        except Exception as e:
            _LOGGER.error("ERROR LedFx send command %r", e)

        self.async_schedule_update_ha_state(True)

class EffectEntity(Entity):
    @property
    def entity_category(self) -> str:
        return ENTITY_CATEGORY_CONFIG

    @property
    def available(self) -> bool:
        return self._device.is_available and self._is_available \
               and self._device.last_effect.is_support_entity(self._id) \
               and self._device.get_entity_data(self._id)["is_available"]

class EffectSwitch(EffectEntity, LedFxSwitch):
    async def async_turn_on(self, **kwargs) -> None:
        await self.async_send(True)
        self._device.update_entity_data(self._id, "is_on", True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.async_send(False)
        self._device.update_entity_data(self._id, "is_on", False)

class EffectNumber(NumberEntity, EffectEntity, LedFxEntity):
    @property
    def value(self) -> Optional[float]:
        return self._device.get_entity_data(self._id)["value"]

    @property
    def min_value(self) -> float:
        if not self.available or self._device.get_entity_data(self._id)["minimum"] is None:
            return DEFAULT_MIN_VALUE

        return self._device.get_entity_data(self._id)["minimum"]

    @property
    def max_value(self) -> float:
        if not self.available or self._device.get_entity_data(self._id)["maximum"] is None:
            return DEFAULT_MAX_VALUE

        return self._device.get_entity_data(self._id)["maximum"]

    @property
    def step(self) -> float:
        return self.min_value

    @property
    def mode(self) -> str:
        return "slider"

    async def async_set_value(self, value: float) -> None:
        await self.async_send(value)

class EffectSelect(EffectEntity, LedFxSelect):
    async def async_select_option(self, value: str) -> None:
        await self.async_send(value)

class AudioInput(LedFxSelect):
    async def async_select_option(self, value: str) -> None:
        if not self.available or value not in self.options:
            return

        try:
            await self._device.api.set_audio_device(self.options.index(value) + 1)

            self._device.get_entity_data(self._id)["current_option"] = value
        except Exception as e:
            _LOGGER.error("ERROR LedFx send command %r", e)