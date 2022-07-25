"""Light component."""


from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ENTITY_ID_FORMAT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_EFFECT,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_LIGHT_BRIGHTNESS,
    ATTR_LIGHT_CONFIG,
    ATTR_LIGHT_CUSTOM_PRESETS,
    ATTR_LIGHT_DEFAULT_PRESETS,
    ATTR_LIGHT_EFFECT,
    ATTR_LIGHT_EFFECT_CONFIG,
    ATTR_LIGHT_EFFECTS,
    ATTR_LIGHT_STATE,
    ATTR_STATE,
    SIGNAL_NEW_DEVICE,
)
from .entity import LedFxEntity
from .enum import ActionType, EffectCategory
from .helper import build_effects, find_effect
from .updater import (
    LedFxEntityDescription,
    LedFxUpdater,
    async_get_updater,
    convert_brightness,
)

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LedFx light entry.

    :param hass: HomeAssistant: Home Assistant object
    :param config_entry: ConfigEntry: ConfigEntry object
    :param async_add_entities: AddEntitiesCallback: AddEntitiesCallback callback object
    """

    updater: LedFxUpdater = async_get_updater(hass, config_entry.entry_id)

    @callback
    def add_device(entity: LedFxEntityDescription) -> None:
        """Add device.

        :param entity: LedFxEntityDescription: Sensor object
        """

        async_add_entities(
            [
                LedFxLight(
                    f"{config_entry.entry_id}-{entity.description.key}",
                    entity,
                    updater,
                )
            ]
        )

    for device in updater.devices.values():
        add_device(device)

    updater.new_device_callback = async_dispatcher_connect(
        hass, SIGNAL_NEW_DEVICE, add_device
    )


class LedFxLight(LedFxEntity, LightEntity):
    """LedFx light entry."""

    _type: ActionType

    def __init__(
        self,
        unique_id: str,
        entity: LedFxEntityDescription,
        updater: LedFxUpdater,
    ) -> None:
        """Initialize button.

        :param unique_id: str: Unique ID
        :param entity: LedFxEntityDescription object
        :param updater: LedFxUpdater: Luci updater object
        """

        LedFxEntity.__init__(
            self, unique_id, entity.description, updater, ENTITY_ID_FORMAT
        )

        self._type = entity.type
        self._attr_device_code = entity.description.key

        self._attr_device_info = entity.device_info
        self._attr_supported_features = SUPPORT_EFFECT | SUPPORT_BRIGHTNESS

        self._attr_is_on = updater.data.get(
            f"{self._attr_device_code}_{ATTR_LIGHT_STATE}", False
        )
        self._attr_brightness = min(
            updater.data.get(f"{self._attr_device_code}_{ATTR_LIGHT_BRIGHTNESS}", 0),
            255,
        )
        self._attr_effect_list = build_effects(
            updater.data.get(ATTR_LIGHT_EFFECTS, []),
            updater.data.get(ATTR_LIGHT_DEFAULT_PRESETS, {}),
            updater.data.get(ATTR_LIGHT_CUSTOM_PRESETS, {}),
        )
        self._attr_effect = updater.data.get(
            f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT}"
        )
        self._attr_extra_state_attributes = updater.data.get(
            f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT_CONFIG}", {}
        ) | updater.data.get(f"{self._attr_device_code}_{ATTR_LIGHT_CONFIG}", {})

    def _handle_coordinator_update(self) -> None:
        """Update state."""

        is_available: bool = self._updater.data.get(ATTR_STATE, False)

        is_on: bool = self._updater.data.get(
            f"{self._attr_device_code}_{ATTR_LIGHT_STATE}", False
        )
        brightness: int = min(
            self._updater.data.get(
                f"{self._attr_device_code}_{ATTR_LIGHT_BRIGHTNESS}", 0
            ),
            255,
        )
        effect_list = build_effects(
            self._updater.data.get(ATTR_LIGHT_EFFECTS, []),
            self._updater.data.get(ATTR_LIGHT_DEFAULT_PRESETS, {}),
            self._updater.data.get(ATTR_LIGHT_CUSTOM_PRESETS, {}),
        )
        effect: str | None = self._updater.data.get(
            f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT}"
        )
        attributes: dict = {
            code: value
            for code, value in self._updater.data.get(
                f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT_CONFIG}", {}
            ).items()
            if code != ATTR_BRIGHTNESS
        } | self._updater.data.get(f"{self._attr_device_code}_{ATTR_LIGHT_CONFIG}", {})

        if (  # pylint: disable=too-many-boolean-expressions
            self._attr_is_on == is_on
            and self._attr_available == is_available
            and self._attr_brightness == brightness
            and self._attr_effect == effect
            and self._attr_effect_list == effect_list
            and self._attr_extra_state_attributes == attributes
        ):
            return

        self._attr_available = is_available
        self._attr_is_on = is_on
        self._attr_brightness = brightness
        self._attr_effect_list = effect_list
        self._attr_effect = effect
        self._attr_extra_state_attributes = attributes

        self.async_write_ha_state()

    async def _device_on(self, **kwargs: Any) -> None:
        """Device on action

        :param kwargs: Any: Any arguments
        """

        preset: str | None = None
        old_effect: str | None = self._attr_effect
        category: EffectCategory = EffectCategory.NONE

        if ATTR_EFFECT in kwargs:
            self._attr_effect, preset, category = find_effect(
                kwargs[ATTR_EFFECT],
                self._updater.data.get(ATTR_LIGHT_DEFAULT_PRESETS, []),
                self._updater.data.get(ATTR_LIGHT_CUSTOM_PRESETS, []),
            )

        if (
            self._attr_effect != old_effect
            or not self._attr_is_on
            or preset is not None
        ):
            response: dict = dict(
                await self._updater.client.preset(
                    self._attr_device_code,  # type: ignore
                    category.value,
                    self._attr_effect,  # type: ignore
                    preset,  # type: ignore
                )
                if category != EffectCategory.NONE and preset is not None
                else await self._updater.client.device_on(
                    self._attr_device_code, self._attr_effect  # type: ignore
                )
            )

            effect_config: dict = {}
            if "effect" in response:
                effect_config = {
                    key: value
                    for key, value in response["effect"].get("config", {}).items()
                    if not isinstance(value, dict) and not isinstance(value, list)
                }

            self._updater.data[
                f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT}"
            ] = self._attr_effect

            self._updater.data[
                f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT_CONFIG}"
            ] = {
                code: value
                for code, value in effect_config.items()
                if code != ATTR_BRIGHTNESS
            }

        if ATTR_BRIGHTNESS not in kwargs:
            return

        await self.async_update_effect(
            ATTR_BRIGHTNESS, convert_brightness(float(kwargs[ATTR_BRIGHTNESS]))
        )

    async def _device_off(self, **kwargs: Any) -> None:
        """Device off action

        :param kwargs: Any: Any arguments
        """

        await self._updater.client.device_off(self._attr_device_code)  # type: ignore

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on action

        :param kwargs: Any: Any arguments
        """

        await self._async_call(f"_{self._type}_{STATE_ON}", STATE_ON, **kwargs)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off action

        :param kwargs: Any: Any arguments
        """

        await self._async_call(f"_{self._type}_{STATE_OFF}", STATE_OFF, **kwargs)

    async def _async_call(self, method: str, state: str, **kwargs: Any) -> None:
        """Async turn action

        :param method: str: Call method
        :param state: str: Call state
        :param kwargs: Any: Any arguments
        """

        if action := getattr(self, method):
            await action(**kwargs)

            self._updater.data[f"{self._attr_device_code}_{ATTR_LIGHT_STATE}"] = (
                state == STATE_ON
            )
            self._attr_is_on = state == STATE_ON

            if ATTR_BRIGHTNESS in kwargs:
                self._updater.data[
                    f"{self._attr_device_code}_{ATTR_LIGHT_BRIGHTNESS}"
                ] = kwargs[ATTR_BRIGHTNESS]
                self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

            self._attr_extra_state_attributes = {
                code: value
                for code, value in self._updater.data.get(
                    f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT_CONFIG}", {}
                ).items()
                if code != ATTR_BRIGHTNESS
            } | self._updater.data.get(
                f"{self._attr_device_code}_{ATTR_LIGHT_CONFIG}", {}
            )

            if ATTR_BRIGHTNESS not in kwargs:
                self._updater.async_update_listeners()

            self.async_write_ha_state()
