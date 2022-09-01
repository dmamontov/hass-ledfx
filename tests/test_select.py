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
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_OPTION,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
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
from tests.setup import MultipleSideEffect, async_mock_client, async_setup

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
        await async_mock_client(mock_client)

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        state: State = hass.states.get(
            _generate_id(ATTR_SELECT_AUDIO_INPUT_NAME, updater.ip)
        )
        assert state.state == "USB PnP Sound Device: Audio (hw:0,0)"
        assert state.name == ATTR_SELECT_AUDIO_INPUT_NAME
        assert state.attributes["icon"] == "mdi:audio-input-stereo-minijack"
        assert state.attributes["attribution"] == ATTRIBUTION
        assert state.attributes["options"] == [
            "USB PnP Sound Device: Audio (hw:0,0)",
            "sysdefault",
            "spdif",
            "samplerate",
            "speexrate",
            "upmix",
            "vdownmix",
            "default",
        ]


async def test_update_audio_devices(hass: HomeAssistant) -> None:
    """Test update audio_devices.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client, patch(
        "custom_components.ledfx.updater.async_dispatcher_send"
    ):
        await async_mock_client(mock_client)

        def error() -> None:
            raise LedFxRequestError

        def original_device() -> dict:
            return json.loads(load_fixture("audio_devices_data.json"))

        def changed_device() -> dict:
            return json.loads(load_fixture("audio_devices_change_data.json"))

        mock_client.return_value.audio_devices = AsyncMock(
            side_effect=MultipleSideEffect(
                original_device, original_device, changed_device
            )
        )

        def original_config() -> dict:
            return json.loads(load_fixture("config_data.json"))

        def changed_config() -> dict:
            return json.loads(load_fixture("config_change_data.json"))

        mock_client.return_value.config = AsyncMock(
            side_effect=MultipleSideEffect(
                original_config, original_config, changed_config, error
            )
        )

        def success_set(index: int, is_virtual: bool = False) -> dict:
            assert index == 5
            return json.loads(load_fixture("set_audio_device_data.json"))

        def error_set(index: int, is_virtual: bool = False) -> dict:
            assert index == 3
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
        assert state.state == "USB PnP Sound Device: Audio (hw:0,0)"
        assert state.name == ATTR_SELECT_AUDIO_INPUT_NAME
        assert state.attributes["options"] == [
            "USB PnP Sound Device: Audio (hw:0,0)",
            "sysdefault",
            "spdif",
            "samplerate",
            "speexrate",
            "upmix",
            "vdownmix",
            "default",
        ]
        assert entry is not None
        assert entry.entity_category == EntityCategory.CONFIG

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        state = hass.states.get(unique_id)
        assert state.state == "spdif"
        assert state.name == ATTR_SELECT_AUDIO_INPUT_NAME
        assert state.attributes["options"] == [
            "USB PnP Sound Device: Audio (hw:0,0)",
            "sysdefault",
            "spdif",
            "samplerate",
        ]

        assert await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "samplerate"},
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == "samplerate"

        assert await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "sysdefault"},
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == "samplerate"

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
        await async_mock_client(mock_client)

        def success_effect(
            device_code: str, effect: str, config: dict, is_virtual: bool = False
        ) -> dict:
            assert device_code == "wled"
            assert effect == "gradient"
            assert config == {
                "background_color": "tan",
                "blur": 0.0,
                "brightness": 1.0,
                "flip": False,
                "gradient_name": "Rainbow",
                "gradient_repeat": 1,
                "gradient_roll": 0,
                "mirror": False,
                "modulate": False,
                "modulation_effect": "sine",
                "modulation_speed": 0.5,
                "speed": 1.0,
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

        unique_id: str = _generate_id("wled_background_color", updater.ip)
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
        assert state.state == "black"
        assert state.name == "Background Color"
        assert state.attributes["icon"] == "mdi:format-color-fill"
        assert state.attributes["options"] == [
            "black",
            "blue",
            "blue-aqua",
            "blue-light",
            "blue-navy",
            "brown",
            "cyan",
            "gold",
            "green",
            "green-coral",
            "green-forest",
            "green-spring",
            "green-teal",
            "green-turquoise",
            "hotpink",
            "lightblue",
            "lightgreen",
            "lightpink",
            "lightyellow",
            "magenta",
            "maroon",
            "mint",
            "olive",
            "orange",
            "orange-deep",
            "peach",
            "pink",
            "plum",
            "purple",
            "red",
            "sepia",
            "skyblue",
            "steelblue",
            "tan",
            "violetred",
            "white",
            "yellow",
            "yellow-acid",
        ]
        assert state.attributes["attribution"] == ATTRIBUTION

        assert await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "tan"},
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
                {ATTR_ENTITY_ID: [unique_id], ATTR_OPTION: "yellow-acid"},
                blocking=True,
                limit=None,
            )


async def test_new_effect_property(hass: HomeAssistant) -> None:
    """Test new effect property.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success() -> dict:
            return json.loads(load_fixture("schema_data.json"))

        def success_two() -> dict:
            return json.loads(load_fixture("schema_changed_data.json"))

        mock_client.return_value.schema = AsyncMock(
            side_effect=MultipleSideEffect(
                success, success_two, success_two, success_two
            )
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("wled_new_select", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        unique_id = _generate_id("ambi_new_select", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        unique_id = _generate_id("garland_2_new_select", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        unique_id = _generate_id("wled_new_select", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)
        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)

        unique_id = _generate_id("ambi_new_select", updater.ip)
        entry = registry.async_get(unique_id)
        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)

        unique_id = _generate_id("garland_2_new_select", updater.ip)
        entry = registry.async_get(unique_id)
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

        unique_id = _generate_id("wled_new_select", updater.ip)
        state: State = hass.states.get(unique_id)
        assert state.state == STATE_UNKNOWN
        assert state.name == "New select"
        assert state.attributes["options"] == ["breath", "sine"]
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("ambi_new_select", updater.ip)
        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "New select"
        assert state.attributes["options"] == ["breath", "sine"]
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("garland_2_new_select", updater.ip)
        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "New select"
        assert state.attributes["options"] == ["breath", "sine"]
        assert state.attributes["attribution"] == ATTRIBUTION


async def test_effect_incorrect_property(hass: HomeAssistant) -> None:
    """Test effect incorrect property.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("wled_align", updater.ip)
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
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "Align"
        assert state.attributes["icon"] == "mdi:format-vertical-align-center"
        assert state.attributes["options"] == ["center", "invert", "left", "right"]
        assert state.attributes["attribution"] == ATTRIBUTION


async def test_effect_property_disabled_light(hass: HomeAssistant) -> None:
    """Test effect property disabled light.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("ambi_align", updater.ip)
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
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "Align"
        assert state.attributes["icon"] == "mdi:format-vertical-align-center"
        assert state.attributes["options"] == ["center", "invert", "left", "right"]
        assert state.attributes["attribution"] == ATTRIBUTION


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
