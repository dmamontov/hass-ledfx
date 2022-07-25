"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines

from __future__ import annotations

import json
import logging
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import load_fixture

from custom_components.ledfx.const import ATTR_SELECT_AUDIO_INPUT, DOMAIN, UPDATER
from custom_components.ledfx.updater import LedFxUpdater, async_get_updater
from tests.setup import async_mock_client, async_setup

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""

    yield


async def test_updater_schedule(hass: HomeAssistant) -> None:
    """Test updater schedule.

    :param hass: HomeAssistant
    """

    updater, _ = await async_setup(hass)

    assert updater._unsub_refresh is None

    updater.schedule_refresh(updater._update_interval)
    updater.schedule_refresh(updater._update_interval)

    assert updater._unsub_refresh is not None


async def test_updater_incorrect_effect_field(hass: HomeAssistant) -> None:
    """Test updater incorrect effect field.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        mock_client.return_value.schema = AsyncMock(
            return_value=json.loads(load_fixture("schema_undefined_data.json"))
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success
        assert "test" not in updater.effect_properties


async def test_updater_incorrect_config(hass: HomeAssistant) -> None:
    """Test updater incorrect config.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(load_fixture("config_incorrect_data.json"))
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

        assert updater.last_update_success
        assert ATTR_SELECT_AUDIO_INPUT not in updater.data


async def test_updater_get_updater(hass: HomeAssistant) -> None:
    """Test updater get updater.

    :param hass: HomeAssistant
    """

    with patch("custom_components.ledfx.updater.LedFxClient") as mock_client:
        await async_mock_client(mock_client)

        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(load_fixture("config_incorrect_data.json"))
        )

        _, config_entry = await async_setup(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.data[DOMAIN][config_entry.entry_id][UPDATER] == async_get_updater(
            hass, config_entry.entry_id
        )

        with pytest.raises(ValueError):
            async_get_updater(hass, "incorrect")
