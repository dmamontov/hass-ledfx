"""Media player component."""

from __future__ import annotations

from homeassistant.components.media_player import (
    ENTITY_ID_FORMAT,
    MediaPlayerEntity,
    MediaPlayerEntityDescription,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_STATE
from .entity import LedFxEntity
from .updater import LedFxUpdater, async_get_updater

MEDIA_PLAYERS: tuple[MediaPlayerEntityDescription, ...] = (
    MediaPlayerEntityDescription(
        key="media_player",
        name="LedFx media player",
        device_class="tv",
        entity_registry_enabled_default=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LedFx media player entry.

    :param hass: HomeAssistant: Home Assistant object
    :param config_entry: ConfigEntry: Config Entry object
    :param async_add_entities: AddEntitiesCallback: Async add callback
    """

    updater: LedFxUpdater = async_get_updater(hass, config_entry.entry_id)

    entities: list[LedFxMediaPlayer] = [
        LedFxMediaPlayer(
            f"{config_entry.entry_id}-{description.key}",
            description,
            updater,
        )
        for description in MEDIA_PLAYERS
    ]
    async_add_entities(entities)


class LedFxMediaPlayer(LedFxEntity, MediaPlayerEntity):
    """LedFx media player entry."""

    def __init__(
        self,
        unique_id: str,
        description: MediaPlayerEntityDescription,
        updater: LedFxUpdater,
    ) -> None:
        """Initialize media player.

        :param unique_id: str: Unique ID
        :param description: MediaPlayerEntityDescription: MediaPlayerEntityDescription object
        :param updater: LedFxUpdater: LedFx updater object
        """

        LedFxEntity.__init__(self, unique_id, description, updater, ENTITY_ID_FORMAT)

        self._supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
        )

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Supported features."""
        return self._supported_features

    def _handle_coordinator_update(self) -> None:
        """Update state."""

        if self._updater.data.get("paused"):
            self._attr_state = MediaPlayerState.PAUSED
        else:
            self._attr_state = MediaPlayerState.PLAYING

        self.async_write_ha_state()

    async def async_media_play(self) -> None:
        """Play media."""
        await self._updater.client.toggle_play_pause()

    async def async_media_pause(self) -> None:
        """Pause media."""
        await self._updater.client.toggle_play_pause()
