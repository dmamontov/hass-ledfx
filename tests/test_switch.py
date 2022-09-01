"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines,too-many-locals

from __future__ import annotations

import json
import logging
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.switch import ENTITY_ID_FORMAT as SWITCH_ENTITY_ID_FORMAT
from homeassistant.components.switch import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_UNAVAILABLE
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


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""

    yield


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
                "background_color": "black",
                "blur": 0.0,
                "brightness": 1.0,
                "flip": True,
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

        def success_effect_two(
            device_code: str, effect: str, config: dict, is_virtual: bool = False
        ) -> dict:
            assert device_code == "wled"
            assert effect == "gradient"
            assert config == {
                "background_color": "black",
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
            side_effect=MultipleSideEffect(
                success_effect, success_effect_two, error_effect
            )
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("wled_flip", updater.ip)
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
        assert state.state == STATE_OFF
        assert state.name == "Flip"
        assert state.attributes["icon"] == "mdi:flip-horizontal"
        assert state.attributes["attribution"] == ATTRIBUTION

        assert await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: [unique_id]},
            blocking=True,
            limit=None,
        )

        assert await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: [unique_id]},
            blocking=True,
            limit=None,
        )

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()
        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        with pytest.raises(LedFxRequestError):
            assert await hass.services.async_call(
                SWITCH_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: [unique_id]},
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

        unique_id: str = _generate_id("wled_new_switch", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        unique_id = _generate_id("ambi_new_switch", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        unique_id = _generate_id("garland_2_new_switch", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        unique_id = _generate_id("wled_new_switch", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)
        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)

        unique_id = _generate_id("ambi_new_switch", updater.ip)
        entry = registry.async_get(unique_id)
        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)

        unique_id = _generate_id("garland_2_new_switch", updater.ip)
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

        unique_id = _generate_id("wled_new_switch", updater.ip)
        state = hass.states.get(unique_id)
        assert state.state == STATE_OFF
        assert state.name == "New switch"
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("ambi_new_switch", updater.ip)
        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "New switch"
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("garland_2_new_switch", updater.ip)
        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "New switch"
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

        unique_id: str = _generate_id("wled_sparks", updater.ip)
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
        assert state.name == "Sparks"
        assert state.attributes["icon"] == "mdi:shimmer"
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

        unique_id: str = _generate_id("ambi_sparks", updater.ip)
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
        assert state.name == "Sparks"
        assert state.attributes["icon"] == "mdi:shimmer"
        assert state.attributes["attribution"] == ATTRIBUTION


def _generate_id(code: str, ip_address: str) -> str:
    """Generate unique id

    :param code: str
    :param ip_address: str
    :return str
    """

    return generate_entity_id(
        SWITCH_ENTITY_ID_FORMAT,
        ip_address,
        code,
    )
