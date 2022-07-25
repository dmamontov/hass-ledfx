"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines,too-many-locals

from __future__ import annotations

import json
import logging
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.number import ATTR_VALUE
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.number import ENTITY_ID_FORMAT as NUMBER_ENTITY_ID_FORMAT
from homeassistant.components.number import SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
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

        def success_effect(device_code: str, effect: str, config: dict) -> dict:
            assert device_code == "wled"
            assert effect == "gradient"
            assert config == {
                "background_color": "black",
                "blur": 9.0,
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

        def error_effect(device_code: str, effect: str, config: dict) -> None:
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

        unique_id: str = _generate_id("wled_blur", updater.ip)
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
        assert float(state.state) == 0.0
        assert state.name == "Blur"
        assert state.attributes["icon"] == "mdi:blur"
        assert state.attributes["min"] == 0.0
        assert state.attributes["max"] == 10.0
        assert state.attributes["step"] == 0.1
        assert state.attributes["attribution"] == ATTRIBUTION

        assert await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: [unique_id], ATTR_VALUE: 9.0},
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
                NUMBER_DOMAIN,
                SERVICE_SET_VALUE,
                {ATTR_ENTITY_ID: [unique_id], ATTR_VALUE: 10.0},
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

        unique_id: str = _generate_id("wled_new_number", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        unique_id = _generate_id("ambi_new_number", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        unique_id = _generate_id("garland_2_new_number", updater.ip)
        assert hass.states.get(unique_id) is None
        assert registry.async_get(unique_id) is None

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        unique_id = _generate_id("wled_new_number", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)
        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)

        unique_id = _generate_id("ambi_new_number", updater.ip)
        entry = registry.async_get(unique_id)
        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)

        unique_id = _generate_id("garland_2_new_number", updater.ip)
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

        unique_id = _generate_id("wled_new_number", updater.ip)
        state: State = hass.states.get(unique_id)
        assert state.state == STATE_UNKNOWN
        assert state.name == "New number"
        assert state.attributes["min"] == 0.0
        assert state.attributes["max"] == 10.0
        assert state.attributes["step"] == 0.1
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("ambi_new_number", updater.ip)
        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "New number"
        assert state.attributes["min"] == 0.0
        assert state.attributes["max"] == 10.0
        assert state.attributes["step"] == 0.1
        assert state.attributes["attribution"] == ATTRIBUTION

        unique_id = _generate_id("garland_2_new_number", updater.ip)
        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE
        assert state.name == "New number"
        assert state.attributes["min"] == 0.0
        assert state.attributes["max"] == 10.0
        assert state.attributes["step"] == 0.1
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

        unique_id: str = _generate_id("wled_band_count", updater.ip)
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
        assert state.name == "Band Count"
        assert state.attributes["icon"] == "mdi:counter"
        assert state.attributes["min"] == 1.0
        assert state.attributes["max"] == 16.0
        assert state.attributes["step"] == 1.0
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

        unique_id: str = _generate_id("ambi_band_count", updater.ip)
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
        assert state.name == "Band Count"
        assert state.attributes["icon"] == "mdi:counter"
        assert state.attributes["min"] == 1.0
        assert state.attributes["max"] == 16.0
        assert state.attributes["step"] == 1.0
        assert state.attributes["attribution"] == ATTRIBUTION


def _generate_id(code: str, ip_address: str) -> str:
    """Generate unique id

    :param code: str
    :param ip_address: str
    :return str
    """

    return generate_entity_id(
        NUMBER_ENTITY_ID_FORMAT,
        ip_address,
        code,
    )
