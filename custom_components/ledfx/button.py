"""Button component."""

from __future__ import annotations

import logging

from homeassistant.components.button import ENTITY_ID_FORMAT, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_STATE, SIGNAL_NEW_BUTTON
from .entity import LedFxEntity
from .enum import ActionType
from .updater import LedFxEntityDescription, LedFxUpdater, async_get_updater

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LedFx button entry.

    :param hass: HomeAssistant: Home Assistant object
    :param config_entry: ConfigEntry: Config Entry object
    :param async_add_entities: AddEntitiesCallback: Async add callback
    """

    updater: LedFxUpdater = async_get_updater(hass, config_entry.entry_id)

    @callback
    def add_button(entity: LedFxEntityDescription) -> None:
        """Add button.

        :param entity: LedFxEntityDescription: Sensor object
        """

        async_add_entities(
            [
                LedFxButton(
                    f"{config_entry.entry_id}-{entity.description.key}",
                    entity,
                    updater,
                )
            ]
        )

    for button in updater.buttons.values():
        add_button(button)

    updater.new_button_callback = async_dispatcher_connect(
        hass, SIGNAL_NEW_BUTTON, add_button
    )


# pylint: disable=too-many-ancestors
class LedFxButton(LedFxEntity, ButtonEntity):
    """LedFx button entry."""

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

        self._attr_device_info = entity.device_info
        self._type = entity.type

    def _handle_coordinator_update(self) -> None:
        """Update state."""

        is_available: bool = self._updater.data.get(ATTR_STATE, False)

        if self._attr_available == is_available:  # type: ignore
            return

        self._attr_available = is_available

        self.async_write_ha_state()

    async def _scene_press(self) -> None:
        """Press scene."""

        await self._updater.client.run_scene(self.entity_description.key)

    async def async_press(self) -> None:
        """Async press action."""

        if action := getattr(self, f"_{self._type}_press"):
            await action()
