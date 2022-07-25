"""MiWifi entity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LIGHT_BRIGHTNESS,
    ATTR_LIGHT_EFFECT,
    ATTR_LIGHT_EFFECT_CONFIG,
    ATTR_STATE,
    ATTRIBUTION,
)
from .helper import generate_entity_id
from .updater import LedFxUpdater, convert_brightness

_LOGGER = logging.getLogger(__name__)


class LedFxEntity(CoordinatorEntity):
    """LedFx entity."""

    _attr_attribution: str = ATTRIBUTION
    _attr_device_code: str | None = None

    def __init__(
        self,
        unique_id: str,
        description: EntityDescription,
        updater: LedFxUpdater,
        entity_id_format: str,
    ) -> None:
        """Initialize sensor.

        :param unique_id: str: Unique ID
        :param description: EntityDescription: EntityDescription object
        :param updater: LedFxUpdater: LedFx updater object
        :param entity_id_format: str: ENTITY_ID_FORMAT
        """

        CoordinatorEntity.__init__(self, coordinator=updater)

        self.entity_description = description
        self._updater: LedFxUpdater = updater

        self.entity_id = generate_entity_id(
            entity_id_format,
            updater.ip,
            description.key,
        )

        self._attr_name = description.name
        self._attr_unique_id = unique_id
        self._attr_available = updater.data.get(ATTR_STATE, False)

        self._attr_device_info = updater.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""

        await CoordinatorEntity.async_added_to_hass(self)

    @property
    def available(self) -> bool:
        """Is available

        :return bool: Is available
        """

        return self._attr_available and self.coordinator.last_update_success

    def _handle_coordinator_update(self) -> None:
        """Update state."""

        raise NotImplementedError  # pragma: no cover

    async def async_update_effect(
        self,
        code: str,
        value: Any = None,
    ) -> None:
        """Update effect

        :param code: str: Code
        :param value: Any: Value
        """

        config: dict = dict(
            self._updater.data.get(
                f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT_CONFIG}", {}
            )
            | {
                ATTR_BRIGHTNESS: convert_brightness(
                    min(
                        float(
                            self._updater.data.get(
                                f"{self._attr_device_code}_{ATTR_LIGHT_BRIGHTNESS}", 0
                            )
                        ),
                        255,
                    )
                )
            }
            | {code: value}
        )

        effect: str | None = self._updater.data.get(
            f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT}"
        )

        if self._attr_device_code and effect:
            await self._updater.client.effect(
                self._attr_device_code,
                effect,
                config,
            )

            self._updater.data[
                f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT_CONFIG}"
            ] = {
                code: value for code, value in config.items() if code != ATTR_BRIGHTNESS
            }

            self._updater.async_update_listeners()
