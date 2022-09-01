"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines,too-many-locals

from __future__ import annotations

import json
import logging
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.select import ENTITY_ID_FORMAT as SELECT_ENTITY_ID_FORMAT
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.const import ATTR_ENTITY_ID, ATTR_OPTION, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    load_fixture,
)

from custom_components.ledfx.const import (
    ATTR_SELECT_AUDIO_INPUT_NAME,
    ATTRIBUTION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    UPDATER,
)
from custom_components.ledfx.exceptions import LedFxRequestError
from custom_components.ledfx.helper import generate_entity_id
from custom_components.ledfx.updater import LedFxUpdater
from tests.setup import MultipleSideEffect, async_mock_client_2, async_setup

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""

    yield


async def test_init(hass: HomeAssistant) -> None:
    """Test init.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client, patch(
        "custom_components.ledfx.updater.async_dispatcher_send"
    ):
        await async_mock_client_2(mock_client)

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        state: State = hass.states.get(
            _generate_id(ATTR_SELECT_AUDIO_INPUT_NAME, updater.ip)
        )
        assert state.state == "ALSA: KT USB Audio: - (hw:1,0)"
        assert state.name == ATTR_SELECT_AUDIO_INPUT_NAME
        assert state.attributes["icon"] == "mdi:audio-input-stereo-minijack"
        assert state.attributes["attribution"] == ATTRIBUTION
        assert state.attributes["options"] == [
            "ALSA: KT USB Audio: - (hw:1,0)",
            "ALSA: pulse",
            "ALSA: default",
        ]


async def test_update_audio_devices(hass: HomeAssistant) -> None:
    """Test update audio_devices.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client, patch(
        "custom_components.ledfx.updater.async_dispatcher_send"
    ):
        await async_mock_client_2(mock_client)

        def error() -> None:
            raise LedFxRequestError

        def original_config() -> dict:
            return json.loads(load_fixture("config_v2_data.json"))

        def changed_config() -> dict:
            return json.loads(load_fixture("config_v2_change_data.json"))

        mock_client.return_value.config = AsyncMock(
            side_effect=MultipleSideEffect(
                original_config, original_config, changed_config, error
            )
        )

        def success_set(index: int, is_virtual: bool = False) -> dict:
            assert is_virtual
            assert index == 9
            return json.loads(load_fixture("set_audio_device_data.json"))

        def error_set(index: int, is_virtual: bool = False) -> dict:
            assert is_virtual
            assert index == 10
            raise LedFxRequestError

        mock_client.return_value.set_audio_device = AsyncMock(
            side_effect=MultipleSideEffect(success_set, error_set)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id(ATTR_SELECT_AUDIO_INPUT_NAME, updater.ip)

        entry: er.RegistryEntry | None = registry.async_get(unique_id)
        state: State = hass.states.get(unique_id)
        assert state.state == "ALSA: KT USB Audio: - (hw:1,0)"
        assert state.name == ATTR_SELECT_AUDIO_INPUT_NAME
        assert state.attributes["options"] == [
            "ALSA: KT USB Audio: - (hw:1,0)",
            "ALSA: pulse",
            "ALSA: default",
        ]
        assert entry is not None
        assert entry.entity_category == EntityCategory.CONFIG

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        state = hass.states.get(unique_id)
        assert state.state == "ALSA: default"
        assert state.name == ATTR_SELECT_AUDIO_INPUT_NAME
        assert state.attributes["options"] == [
            "ALSA: KT USB Audio: - (hw:1,0)",
            "ALSA: pulse",
            "ALSA: default",
        ]

        assert await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "ALSA: pulse"},
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == "ALSA: pulse"

        assert await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "ALSA: default"},
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == "ALSA: pulse"

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE


async def test_effect_property(hass: HomeAssistant) -> None:
    """Test effect property.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client_2(mock_client)

        def success_effect(
            device_code: str, effect: str, config: dict, is_virtual: bool = False
        ) -> dict:
            assert is_virtual
            assert device_code == "wled"
            assert effect == "magnitude"
            assert config == {
                "background_brightness": 1.0,
                "background_color": "#000000",
                "blur": 0.0,
                "brightness": 1.0,
                "flip": False,
                "frequency_range": "Lows (beat+bass)",
                "gradient": (
                    "linear-gradient(90deg, rgb(255, 0, 0) 0%, rgb(255, 120, 0) 14%, "
                    "rgb(255, 200, 0) 28%, rgb(0, 255, 0) 42%, rgb(0, 199, 140) 56%, "
                    "rgb(0, 0, 255) 70%, rgb(128, 0, 128) 84%, rgb(255, 0, 178) 98%)"
                ),
                "gradient_roll": 0.0,
                "mirror": False,
            }

            return json.loads(load_fixture("effect_data.json"))

        def error_effect(
            device_code: str, effect: str, config: dict, is_virtual: bool = False
        ) -> None:
            raise LedFxRequestError

        mock_client.return_value.effect = AsyncMock(
            side_effect=MultipleSideEffect(success_effect, error_effect)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("wled_gradient", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)

        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)
        await hass.async_block_till_done()

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()
        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        state: State = hass.states.get(unique_id)
        assert state.state == "Rainbow"
        assert state.name == "Gradient"
        assert state.attributes["options"] == [
            "Borealis",
            "Dancefloor",
            "Frost",
            "Jungle",
            "Ocean",
            "Plasma",
            "Rainbow",
            "Rust",
            "Spring",
            "Sunset",
            "Viridis",
            "Winamp",
            "Winter",
            "test",
        ]
        assert state.attributes["attribution"] == ATTRIBUTION

        assert await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "Rainbow"},
            blocking=True,
            limit=None,
        )

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        with pytest.raises(LedFxRequestError):
            assert await hass.services.async_call(
                SELECT_DOMAIN,
                SERVICE_SELECT_OPTION,
                {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "Jungle"},
                blocking=True,
                limit=None,
            )


def _generate_id(code: str, ip_address: str) -> str:
    """Generate unique id

    :param code: str
    :param ip_address: str
    :return str
    """

    return generate_entity_id(
        SELECT_ENTITY_ID_FORMAT,
        ip_address,
        code,
    )
