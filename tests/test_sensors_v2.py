"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines

from __future__ import annotations

import json
import logging
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.sensor import ENTITY_ID_FORMAT as SENSOR_ENTITY_ID_FORMAT
from homeassistant.const import STATE_UNAVAILABLE
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
from tests.setup import MultipleSideEffect, async_mock_client_2, async_setup

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""

    yield


@pytest.mark.asyncio
async def test_update_device_sensors_v2(hass: HomeAssistant) -> None:
    """Test update device sensors v2.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client_2(mock_client)

        def success() -> dict:
            return json.loads(load_fixture("config_v2_data.json"))

        def error() -> None:
            raise LedFxRequestError

        mock_client.return_value.config = AsyncMock(
            side_effect=MultipleSideEffect(success, success, success, success, error)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("fft_size", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)

        assert hass.states.get(unique_id) is None
        assert entry is not None
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

        registry.async_update_entity(entity_id=unique_id, disabled_by=None)

        unique_id = _generate_id("mic_rate", updater.ip)
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

        state: State = hass.states.get(_generate_id("fft_size", updater.ip))
        assert state.state == str(4096)
        assert state.name == "fft_size".replace("_", " ").title()
        assert state.attributes["icon"] == "mdi:numeric"
        assert state.attributes["attribution"] == ATTRIBUTION

        state = hass.states.get(_generate_id("mic_rate", updater.ip))
        assert state.state == str(44100)
        assert state.name == "mic_rate".replace("_", " ").title()
        assert state.attributes["icon"] == "mdi:microphone-settings"
        assert state.attributes["attribution"] == ATTRIBUTION

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        state = hass.states.get(_generate_id("fft_size", updater.ip))
        assert state.state == STATE_UNAVAILABLE

        state = hass.states.get(_generate_id("mic_rate", updater.ip))
        assert state.state == STATE_UNAVAILABLE


@pytest.mark.asyncio
async def test_update_new_sensors_v2(hass: HomeAssistant) -> None:
    """Test update new sensors.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client_2(mock_client)

        def success() -> dict:
            return json.loads(load_fixture("config_v2_data.json"))

        def success_two() -> dict:
            return json.loads(load_fixture("config_v2_change_data.json"))

        mock_client.return_value.config = AsyncMock(
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

        unique_id: str = _generate_id("new_sensor", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)

        assert hass.states.get(unique_id) is None
        assert entry is None

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

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

        state = hass.states.get(unique_id)
        assert state.state == "good"
        assert state.name == "new_sensor".replace("_", " ").title()
        assert state.attributes["attribution"] == ATTRIBUTION


def _generate_id(code: str, ip_address: str) -> str:
    """Generate unique id

    :param code: str
    :param ip_address: str
    :return str
    """

    return generate_entity_id(
        SENSOR_ENTITY_ID_FORMAT,
        ip_address,
        code,
    )
