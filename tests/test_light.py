"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Final
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_EFFECT
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.light import ENTITY_ID_FORMAT as LIGHT_ENTITY_ID_FORMAT
from homeassistant.components.light import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    load_fixture,
)

from custom_components.ledfx.const import (
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

EFFECT_LIST: Final = [
    "bands(Reactive)",
    "bands_matrix(Reactive)",
    "** equilizer",
    "bar(Reactive)",
    "* Rainbow-lr",
    "* bouncing-blues",
    "* passing-by",
    "* plasma-cascade",
    "* smooth-bounce",
    "blade_power(Reactive)",
    "blocks(Reactive)",
    "energy(Reactive)",
    "* clear-sky",
    "* smooth-plasma",
    "* smooth-rainbow",
    "* snappy-blues",
    "equalizer(reactive)",
    "fade",
    "* blues",
    "* calm-reds",
    "* rainbow-cycle",
    "* red-to-blue",
    "* sunset",
    "gradient",
    "* Rainbow-roll",
    "* breathing",
    "* falling-blues",
    "* rolling-sunset",
    "* spectrum",
    "* twister",
    "* waves",
    "magnitude(Reactive)",
    "* cold-fire",
    "* jungle-cascade",
    "* lively",
    "* rolling-rainbow",
    "* warm-bass",
    "multiBar(Reactive)",
    "* Rainbow-oscillation",
    "* bright-cascade",
    "* falling-blues",
    "* red-blue-expanse",
    "pitchSpectrum(Reactive)",
    "power(Reactive)",
    "** default",
    "rain(Reactive)",
    "* cold-drops",
    "* meteor-shower",
    "* prismatic",
    "* ripples",
    "* smooth-rwb",
    "rainbow",
    "* cascade",
    "* crawl",
    "* faded",
    "* gentle",
    "* slow-roll",
    "real_strobe(Reactive)",
    "* bass_only",
    "* dancefloor",
    "* extreme",
    "* glitter",
    "* strobe_only",
    "scroll(Reactive)",
    "* cold-crawl",
    "* dynamic-rgb",
    "* fast-hits",
    "* gentle-rgb",
    "* icicles",
    "* rays",
    "* warmth",
    "singleColor",
    "* blue",
    "* cyan",
    "* green",
    "* magenta",
    "* orange",
    "* pink",
    "* red",
    "* red-waves",
    "* steel-pulse",
    "* turquoise-roll",
    "* yellow",
    "spectrum(Reactive)",
    "strobe(Reactive)",
    "* aggro-red",
    "* blues-on-the-beat",
    "* fast-strobe",
    "* faster-strobe",
    "* painful",
    "wavelength(Reactive)",
    "* classic",
    "* greens",
    "* icy",
    "* plasma",
    "* rolling-blues",
    "* rolling-warmth",
    "* sunset-sweep",
]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""

    yield


async def test_devices(hass: HomeAssistant) -> None:
    """Test devices.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success() -> dict:
            return json.loads(load_fixture("devices_data.json"))

        def error() -> None:
            raise LedFxRequestError

        mock_client.return_value.devices = AsyncMock(
            side_effect=MultipleSideEffect(success, error)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id: str = _generate_id("wled", updater.ip)

        state: State = hass.states.get(unique_id)
        assert state.state == STATE_ON
        assert state.name == "Garland #1"
        assert state.attributes["icon"] == "mdi:string-lights"
        assert state.attributes["effect_list"] == EFFECT_LIST
        assert state.attributes["effect"] == "gradient"
        assert state.attributes["background_color"] == "black"
        assert state.attributes["modulation_effect"] == "sine"
        assert state.attributes["gradient_name"] == "Rainbow"
        assert not state.attributes["mirror"]
        assert state.attributes["modulation_speed"] == 0.5
        assert not state.attributes["modulate"]
        assert state.attributes["gradient_repeat"] == 1
        assert not state.attributes["flip"]
        assert state.attributes["gradient_roll"] == 0
        assert state.attributes["speed"] == 1.0
        assert state.attributes["blur"] == 0.0
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("garland_2", updater.ip)

        state = hass.states.get(unique_id)
        assert state.state == STATE_OFF
        assert state.name == "Garland #2"
        assert state.attributes["icon"] == "mdi:string-lights"
        assert state.attributes["effect_list"] == EFFECT_LIST
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("ambi", updater.ip)

        state = hass.states.get(unique_id)
        assert state.state == STATE_OFF
        assert state.name == "Ambilight"
        assert state.attributes["icon"] == "mdi:string-lights"
        assert state.attributes["effect_list"] == EFFECT_LIST
        assert state.attributes["attribution"] == ATTRIBUTION

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        unique_id = _generate_id("wled", updater.ip)

        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE

        unique_id = _generate_id("garland_2", updater.ip)

        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE

        unique_id = _generate_id("ambi", updater.ip)

        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE


async def test_devices_without_custom_preset(hass: HomeAssistant) -> None:
    """Test devices without custom preset.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(
                load_fixture("config_empty_custom_presets_data.json")
            )
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id: str = _generate_id("wled", updater.ip)

        state: State = hass.states.get(unique_id)
        assert state.state == STATE_ON
        assert len(state.attributes["effect_list"]) == len(EFFECT_LIST) - 2

        unique_id = _generate_id("garland_2", updater.ip)

        state = hass.states.get(unique_id)
        assert state.state == STATE_OFF
        assert len(state.attributes["effect_list"]) == len(EFFECT_LIST) - 2

        unique_id = _generate_id("ambi", updater.ip)

        state = hass.states.get(unique_id)
        assert state.state == STATE_OFF
        assert len(state.attributes["effect_list"]) == len(EFFECT_LIST) - 2


async def test_new_devices(hass: HomeAssistant) -> None:
    """Test new_devices.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success() -> dict:
            return json.loads(load_fixture("devices_data.json"))

        def success_two() -> dict:
            return json.loads(load_fixture("devices_changed_data.json"))

        mock_client.return_value.devices = AsyncMock(
            side_effect=MultipleSideEffect(success, success_two)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("new_device", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)

        assert hass.states.get(unique_id) is None
        assert entry is None

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        state = hass.states.get(unique_id)
        assert state.state == STATE_OFF
        assert state.name == "New device"
        assert state.attributes["attribution"] == ATTRIBUTION


async def test_devices_on(hass: HomeAssistant) -> None:
    """Test devices on.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success(device_code: str, effect: str) -> dict:
            assert device_code == "garland-2"
            assert effect == "bands(Reactive)"

            return json.loads(load_fixture("device_on_data.json"))

        def error(device_code: str, effect: str) -> None:
            raise LedFxRequestError

        mock_client.return_value.device_on = AsyncMock(
            side_effect=MultipleSideEffect(success, error)
        )

        def success_effect(device_code: str, effect: str, config: dict) -> dict:
            assert device_code == "garland-2"
            assert effect == "bands(Reactive)"
            assert config == {
                "active": True,
                "background_color": "black",
                "blur": 3.0,
                "brightness": 0.0,
                "flip": False,
                "gradient_name": "Rainbow",
                "gradient_repeat": 1,
                "gradient_roll": 0,
                "isProcessing": False,
                "mirror": False,
                "name": "Wavelength",
                "type": "wavelength(Reactive)",
            }

            return json.loads(load_fixture("effect_data.json"))

        mock_client.return_value.effect = AsyncMock(
            side_effect=MultipleSideEffect(success_effect, success_effect)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id = _generate_id("garland_2", updater.ip)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: [unique_id]},
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == STATE_ON
        assert state.attributes["effect"] == "bands(Reactive)"
        assert state.attributes["gradient_repeat"] == 1
        assert not state.attributes["flip"]
        assert state.attributes["blur"] == 3.0
        assert state.attributes["background_color"] == "black"
        assert state.attributes["gradient_name"] == "Rainbow"
        assert state.attributes["gradient_roll"] == 0
        assert not state.attributes["mirror"]

        with pytest.raises(LedFxRequestError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: [unique_id], ATTR_EFFECT: "wavelength(Reactive)"},
                blocking=True,
                limit=None,
            )


async def test_devices_on_with_effect(hass: HomeAssistant) -> None:
    """Test devices on with effect.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success(device_code: str, effect: str) -> dict:
            assert device_code == "garland-2"
            assert effect == "wavelength(Reactive)"

            return json.loads(load_fixture("device_on_data.json"))

        def error(device_code: str, effect: str) -> None:
            raise LedFxRequestError

        mock_client.return_value.device_on = AsyncMock(
            side_effect=MultipleSideEffect(success, error)
        )

        def success_effect(device_code: str, effect: str, config: dict) -> dict:
            assert device_code == "garland-2"
            assert effect == "wavelength(Reactive)"
            assert config == {
                "active": True,
                "background_color": "black",
                "blur": 3.0,
                "brightness": 0.0,
                "flip": False,
                "gradient_name": "Rainbow",
                "gradient_repeat": 1,
                "gradient_roll": 0,
                "isProcessing": False,
                "mirror": False,
                "name": "Wavelength",
                "type": "wavelength(Reactive)",
            }

            return json.loads(load_fixture("effect_data.json"))

        mock_client.return_value.effect = AsyncMock(
            side_effect=MultipleSideEffect(success_effect, success_effect)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id = _generate_id("garland_2", updater.ip)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: [unique_id], ATTR_EFFECT: "wavelength(Reactive)"},
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == STATE_ON
        assert state.attributes["effect"] == "wavelength(Reactive)"
        assert state.attributes["gradient_repeat"] == 1
        assert not state.attributes["flip"]
        assert state.attributes["blur"] == 3.0
        assert state.attributes["background_color"] == "black"
        assert state.attributes["gradient_name"] == "Rainbow"
        assert state.attributes["gradient_roll"] == 0
        assert not state.attributes["mirror"]

        with pytest.raises(LedFxRequestError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: [unique_id], ATTR_EFFECT: "bar(Reactive)"},
                blocking=True,
                limit=None,
            )


async def test_devices_on_with_effect_and_brightness(hass: HomeAssistant) -> None:
    """Test devices on with effect and brightness.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success(device_code: str, effect: str) -> dict:
            assert device_code == "garland-2"
            assert effect == "wavelength(Reactive)"

            return json.loads(load_fixture("device_on_data.json"))

        mock_client.return_value.device_on = AsyncMock(
            side_effect=MultipleSideEffect(success, success)
        )

        def success_effect(device_code: str, effect: str, config: dict) -> dict:
            assert device_code == "garland-2"
            assert effect == "wavelength(Reactive)"
            assert config == {
                "active": True,
                "background_color": "black",
                "blur": 3.0,
                "brightness": 0.5,
                "flip": False,
                "gradient_name": "Rainbow",
                "gradient_repeat": 1,
                "gradient_roll": 0,
                "isProcessing": False,
                "mirror": False,
                "name": "Wavelength",
                "type": "wavelength(Reactive)",
            }

            return json.loads(load_fixture("effect_data.json"))

        def error_effect(device_code: str, effect: str, config: dict) -> None:
            raise LedFxRequestError

        mock_client.return_value.effect = AsyncMock(
            side_effect=MultipleSideEffect(success_effect, error_effect)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id = _generate_id("garland_2", updater.ip)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: [unique_id],
                ATTR_EFFECT: "wavelength(Reactive)",
                ATTR_BRIGHTNESS: 125,
            },
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == STATE_ON
        assert state.attributes["brightness"] == 125
        assert state.attributes["effect"] == "wavelength(Reactive)"
        assert state.attributes["gradient_repeat"] == 1
        assert not state.attributes["flip"]
        assert state.attributes["blur"] == 3.0
        assert state.attributes["background_color"] == "black"
        assert state.attributes["gradient_name"] == "Rainbow"
        assert state.attributes["gradient_roll"] == 0
        assert not state.attributes["mirror"]

        with pytest.raises(LedFxRequestError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {
                    ATTR_ENTITY_ID: [unique_id],
                    ATTR_EFFECT: "wavelength(Reactive)",
                    ATTR_BRIGHTNESS: 125,
                },
                blocking=True,
                limit=None,
            )


async def test_devices_on_with_preset(hass: HomeAssistant) -> None:
    """Test devices on with preset.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success(device_code: str, category: str, effect: str, preset: str) -> dict:
            assert device_code == "garland-2"
            assert category == "default_presets"
            assert effect == "bar(Reactive)"
            assert preset == "bouncing-blues"

            return json.loads(load_fixture("preset_data.json"))

        def error(device_code: str, category: str, effect: str, preset: str) -> None:
            raise LedFxRequestError

        mock_client.return_value.preset = AsyncMock(
            side_effect=MultipleSideEffect(success, error)
        )

        def success_effect(device_code: str, effect: str, config: dict) -> dict:
            assert device_code == "garland-2"
            assert effect == "bar(Reactive)"
            assert config == {
                "background_color": "black",
                "blur": 8.587469069357562,
                "brightness": 0.0,
                "flip": True,
                "gradient_name": "Sunset",
                "gradient_repeat": 1,
                "gradient_roll": 4,
                "mirror": False,
            }

            return json.loads(load_fixture("effect_data.json"))

        mock_client.return_value.effect = AsyncMock(
            side_effect=MultipleSideEffect(success_effect, success_effect)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id = _generate_id("garland_2", updater.ip)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: [unique_id], ATTR_EFFECT: "* bouncing-blues"},
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == STATE_ON
        assert state.attributes["effect"] == "bar(Reactive)"
        assert state.attributes["blur"] == 8.587469069357562
        assert state.attributes["flip"]
        assert state.attributes["gradient_name"] == "Sunset"
        assert state.attributes["gradient_roll"] == 4
        assert not state.attributes["mirror"]
        assert state.attributes["gradient_repeat"] == 1
        assert state.attributes["background_color"] == "black"

        with pytest.raises(LedFxRequestError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: [unique_id], ATTR_EFFECT: "* bouncing-blues"},
                blocking=True,
                limit=None,
            )


async def test_devices_on_with_preset_and_brightness(hass: HomeAssistant) -> None:
    """Test devices on with preset and brightness.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success(device_code: str, category: str, effect: str, preset: str) -> dict:
            assert device_code == "garland-2"
            assert category == "custom_presets"
            assert effect == "bands_matrix(Reactive)"
            assert preset == "equilizer"

            return json.loads(load_fixture("preset_data.json"))

        mock_client.return_value.preset = AsyncMock(
            side_effect=MultipleSideEffect(success, success)
        )

        def success_effect(device_code: str, effect: str, config: dict) -> dict:
            assert device_code == "garland-2"
            assert effect == "bands_matrix(Reactive)"
            assert config == {
                "background_color": "black",
                "blur": 8.587469069357562,
                "brightness": 0.5,
                "flip": True,
                "gradient_name": "Sunset",
                "gradient_repeat": 1,
                "gradient_roll": 4,
                "mirror": False,
            }

            return json.loads(load_fixture("effect_data.json"))

        def error_effect(device_code: str, effect: str, config: dict) -> None:
            raise LedFxRequestError

        mock_client.return_value.effect = AsyncMock(
            side_effect=MultipleSideEffect(success_effect, error_effect)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id = _generate_id("garland_2", updater.ip)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: [unique_id],
                ATTR_EFFECT: "** equilizer",
                ATTR_BRIGHTNESS: 125,
            },
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == STATE_ON
        assert state.attributes["brightness"] == 125
        assert state.attributes["effect"] == "bands_matrix(Reactive)"
        assert state.attributes["blur"] == 8.587469069357562
        assert state.attributes["flip"]
        assert state.attributes["gradient_name"] == "Sunset"
        assert state.attributes["gradient_roll"] == 4
        assert not state.attributes["mirror"]
        assert state.attributes["gradient_repeat"] == 1
        assert state.attributes["background_color"] == "black"

        with pytest.raises(LedFxRequestError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {
                    ATTR_ENTITY_ID: [unique_id],
                    ATTR_EFFECT: "** equilizer",
                    ATTR_BRIGHTNESS: 125,
                },
                blocking=True,
                limit=None,
            )


async def test_devices_off(hass: HomeAssistant) -> None:
    """Test devices off.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success(device_code: str) -> dict:
            assert device_code == "garland-2"

            return json.loads(load_fixture("device_off_data.json"))

        def error(device_code: str) -> dict:
            raise LedFxRequestError

        mock_client.return_value.device_off = AsyncMock(
            side_effect=MultipleSideEffect(success, error)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id = _generate_id("garland_2", updater.ip)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: [unique_id],
            },
            blocking=True,
            limit=None,
        )

        state = hass.states.get(unique_id)
        assert state.state == STATE_OFF

        with pytest.raises(LedFxRequestError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_OFF,
                {
                    ATTR_ENTITY_ID: [unique_id],
                },
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
        LIGHT_ENTITY_ID_FORMAT,
        ip_address,
        code,
    )
