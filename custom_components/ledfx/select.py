"""Select component."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.select import (
    ENTITY_ID_FORMAT,
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_DEVICE,
    ATTR_FIELD_EFFECTS,
    ATTR_FIELD_OPTIONS,
    ATTR_FIELD_TYPE,
    ATTR_LIGHT_EFFECT,
    ATTR_LIGHT_EFFECT_CONFIG,
    ATTR_LIGHT_STATE,
    ATTR_SELECT_AUDIO_INPUT,
    ATTR_SELECT_AUDIO_INPUT_NAME,
    ATTR_SELECT_AUDIO_INPUT_OPTIONS,
    ATTR_STATE,
    SELECT_ICONS,
    SIGNAL_NEW_SELECT,
)
from .entity import LedFxEntity
from .enum import ActionType, Version
from .exceptions import LedFxError
from .helper import generate_entity_id
from .updater import LedFxEntityDescription, LedFxUpdater, async_get_updater

PARALLEL_UPDATES = 0

OPTIONS_MAP: Final = {
    ATTR_SELECT_AUDIO_INPUT: ATTR_SELECT_AUDIO_INPUT_OPTIONS,
}

SELECTS: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key=ATTR_SELECT_AUDIO_INPUT,
        name=ATTR_SELECT_AUDIO_INPUT_NAME,
        icon="mdi:audio-input-stereo-minijack",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LedFx select entry.

    :param hass: HomeAssistant: Home Assistant object
    :param config_entry: ConfigEntry: ConfigEntry object
    :param async_add_entities: AddEntitiesCallback: AddEntitiesCallback callback object
    """

    updater: LedFxUpdater = async_get_updater(hass, config_entry.entry_id)

    @callback
    def add_select(entity: LedFxEntityDescription) -> None:
        """Add select.

        :param entity: LedFxEntityDescription: Sensor object
        """

        async_add_entities(
            [
                LedFxSelect(
                    f"{config_entry.entry_id}-{entity.device_code}-{entity.description.key}"
                    if entity.type == ActionType.DEVICE
                    else f"{config_entry.entry_id}-{entity.description.key}",
                    entity,
                    updater,
                )
            ]
        )

    for select in SELECTS:
        add_select(
            LedFxEntityDescription(description=select, device_info=updater.device_info)
        )

    for select in updater.selects.values():
        add_select(select)

    updater.new_select_callback = async_dispatcher_connect(
        hass, SIGNAL_NEW_SELECT, add_select
    )


class LedFxSelect(LedFxEntity, SelectEntity):
    """LedFx select entry."""

    _options_key: str
    _type: ActionType

    def __init__(
        self,
        unique_id: str,
        entity: LedFxEntityDescription,
        updater: LedFxUpdater,
    ) -> None:
        """Initialize select.

        :param unique_id: str: Unique ID
        :param entity: LedFxEntityDescription object
        :param updater: LedFxUpdater: Luci updater object
        """

        LedFxEntity.__init__(
            self, unique_id, entity.description, updater, ENTITY_ID_FORMAT
        )

        self._type = entity.type
        self._attr_device_info = entity.device_info
        self._attr_available: bool = True

        if entity.type == ActionType.DEVICE:
            self._attr_device_code = entity.device_code

            self.entity_id = generate_entity_id(
                ENTITY_ID_FORMAT,
                updater.ip,
                f"{entity.device_code}_{entity.description.key}",
            )

            self._attr_current_option = updater.data.get(
                f"{entity.device_code}_{ATTR_LIGHT_EFFECT_CONFIG}", {}
            ).get(entity.description.key)

            self._attr_options = (
                entity.extra.get(ATTR_FIELD_OPTIONS, []) if entity.extra else []
            )

            if entity.extra:
                self._attr_field_type = entity.extra.get(ATTR_FIELD_TYPE)

            self._attr_extra_state_attributes = {
                ATTR_DEVICE: self._attr_device_code,
                ATTR_FIELD_EFFECTS: entity.extra.get(ATTR_FIELD_EFFECTS, [])
                if entity.extra
                else [],
            }

            self._attr_available = bool(
                updater.data.get(ATTR_STATE, False)
                and len(self._attr_options) > 0
                and updater.data.get(f"{self._attr_device_code}_{ATTR_LIGHT_STATE}")
                and updater.data.get(f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT}")
                in self._attr_extra_state_attributes[ATTR_FIELD_EFFECTS]
            )

            if entity.description.key in SELECT_ICONS:
                self._attr_icon = SELECT_ICONS[entity.description.key]

            return

        self._attr_current_option = updater.data.get(entity.description.key, None)

        self._options_key = (
            OPTIONS_MAP[entity.description.key]
            if entity.description.key in OPTIONS_MAP
            else f"{entity.description.key}_options"
        )

        options: dict | list = updater.data.get(self._options_key, [])
        self._attr_options = (
            list(options.values()) if isinstance(options, dict) else options
        )

        self._attr_available = bool(
            updater.data.get(ATTR_STATE, False) and len(self._attr_options) > 0
        )

    def _handle_coordinator_update(self) -> None:
        """Update state."""

        is_available: bool = self._attr_available
        current_option: str = self._attr_current_option
        options: dict | list = self._attr_options

        if self._type == ActionType.DEVICE:
            current_option = self._updater.data.get(
                f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT_CONFIG}", {}
            ).get(self.entity_description.key)

            is_available = bool(
                self._updater.data.get(ATTR_STATE, False)
                and len(options) > 0
                and self._updater.data.get(
                    f"{self._attr_device_code}_{ATTR_LIGHT_STATE}"
                )
                and self._updater.data.get(
                    f"{self._attr_device_code}_{ATTR_LIGHT_EFFECT}"
                )
                in self._attr_extra_state_attributes[ATTR_FIELD_EFFECTS]
            )
        else:
            current_option = self._updater.data.get(self.entity_description.key, False)
            options = self._updater.data.get(self._options_key, [])
            options = list(options.values()) if isinstance(options, dict) else options

            is_available = bool(
                self._updater.data.get(ATTR_STATE, False) and len(options) > 0
            )

        if (
            self._attr_current_option == current_option
            and self._attr_options == options
            and self._attr_available == is_available
        ):
            return

        self._attr_available = is_available
        self._attr_current_option = current_option
        self._attr_options = options

        self.async_write_ha_state()

    async def _audio_input_change(self, option: str) -> bool:
        """Audio input

        :param option: str: Option value
        :return bool: Result
        """

        options: dict = self._updater.data.get(self._options_key, {})
        option_ids: list = [_id for _id, name in options.items() if name == option]

        if option_ids:
            try:
                await self._updater.client.set_audio_device(
                    int(option_ids[0]), self._updater.version == Version.V2
                )

                return True
            except LedFxError as _e:
                _LOGGER.debug("Audio input update error: %r", _e)

        return False

    async def _device_change(self, option: str) -> bool:
        """Device input

        :param option: str: Option value
        :return bool: Result
        """

        await self.async_update_effect(self.entity_description.key, option)

        return True

    async def async_select_option(self, option: str) -> None:
        """Select option

        :param option: str: Option
        """

        code: str = (
            ActionType.DEVICE
            if self._type == ActionType.DEVICE
            else self.entity_description.key
        )

        if action := getattr(self, f"_{code}_change"):
            if await action(option):
                if self._type != ActionType.DEVICE:
                    self._updater.data[self.entity_description.key] = option

                self._attr_current_option = option

            self.async_write_ha_state()
