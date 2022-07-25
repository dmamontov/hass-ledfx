"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines

from __future__ import annotations

import json
import logging
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import ENTITY_ID_FORMAT as BUTTON_ENTITY_ID_FORMAT
from homeassistant.components.button import SERVICE_PRESS
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


async def test_scenes(hass: HomeAssistant) -> None:
    """Test scenes.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success() -> dict:
            return json.loads(load_fixture("scenes_data.json"))

        def error() -> None:
            raise LedFxRequestError

        mock_client.return_value.scenes = AsyncMock(
            side_effect=MultipleSideEffect(success, error)
        )

        def success_run(scene_id: str) -> dict:
            assert scene_id == "test"
            return json.loads(load_fixture("run_scene_data.json"))

        def error_run(scene_id: str) -> None:
            raise LedFxRequestError

        mock_client.return_value.run_scene = AsyncMock(
            side_effect=MultipleSideEffect(success_run, error_run)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success

        unique_id: str = _generate_id("test", updater.ip)

        state: State = hass.states.get(unique_id)
        assert state.state == STATE_UNKNOWN
        assert state.name == "Test"
        assert state.attributes["icon"] == "mdi:image"
        assert state.attributes["attribution"] == ATTRIBUTION

        _prev_calls: int = len(mock_client.mock_calls)

        assert await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: [unique_id]},
            blocking=True,
            limit=None,
        )

        assert len(mock_client.mock_calls) == _prev_calls + 1

        with pytest.raises(LedFxRequestError):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: [unique_id]},
                blocking=True,
                limit=None,
            )

        assert len(mock_client.mock_calls) == _prev_calls + 2

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1)
        )
        await hass.async_block_till_done()

        state = hass.states.get(unique_id)
        assert state.state == STATE_UNAVAILABLE


async def test_new_scene(hass: HomeAssistant) -> None:
    """Test new scene.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        def success() -> dict:
            return json.loads(load_fixture("scenes_data.json"))

        def success_two() -> dict:
            return json.loads(load_fixture("scenes_changed_data.json"))

        mock_client.return_value.scenes = AsyncMock(
            side_effect=MultipleSideEffect(success, success_two)
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]
        registry = er.async_get(hass)

        assert updater.last_update_success

        unique_id: str = _generate_id("new_scene", updater.ip)
        entry: er.RegistryEntry | None = registry.async_get(unique_id)

        assert hass.states.get(unique_id) is None
        assert entry is None

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=DEFAULT_SCAN_INTERVAL + 30)
        )
        await hass.async_block_till_done()

        state = hass.states.get(unique_id)
        assert state.state == STATE_UNKNOWN
        assert state.name == "New Scene"
        assert state.attributes["attribution"] == ATTRIBUTION


def _generate_id(code: str, ip_address: str) -> str:
    """Generate unique id

    :param code: str
    :param ip_address: str
    :return str
    """

    return generate_entity_id(
        BUTTON_ENTITY_ID_FORMAT,
        ip_address,
        code,
    )
