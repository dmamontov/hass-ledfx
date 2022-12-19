"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines

from __future__ import annotations

import logging

import pytest
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import load_fixture
from pytest_httpx import HTTPXMock

from custom_components.ledfx.const import DOMAIN, UPDATER
from custom_components.ledfx.diagnostics import (
    TO_REDACT,
    async_get_config_entry_diagnostics,
)
from custom_components.ledfx.enum import Method
from custom_components.ledfx.updater import LedFxUpdater
from tests.setup import async_setup, get_url

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""

    yield


@pytest.mark.asyncio
async def test_init(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """Test init.

    :param hass: HomeAssistant
    """

    httpx_mock.add_response(
        text=load_fixture("info_data.json"), method=Method.GET, url=get_url("info")
    )
    httpx_mock.add_response(
        text=load_fixture("devices_data.json"),
        method=Method.GET,
        url=get_url("devices"),
    )
    httpx_mock.add_response(
        text=load_fixture("scenes_data.json"), method=Method.GET, url=get_url("scenes")
    )
    httpx_mock.add_response(
        text=load_fixture("audio_devices_data.json"),
        method=Method.GET,
        url=get_url("audio/devices"),
    )
    httpx_mock.add_response(
        text=load_fixture("schema_data.json"), method=Method.GET, url=get_url("schema")
    )
    httpx_mock.add_response(
        text=load_fixture("config_data.json"), method=Method.GET, url=get_url("config")
    )

    _, config_entry = await async_setup(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    updater: LedFxUpdater = hass.data[DOMAIN][config_entry.entry_id][UPDATER]

    assert updater.last_update_success

    diagnostics_data: dict = await async_get_config_entry_diagnostics(
        hass, config_entry
    )

    assert diagnostics_data["config_entry"] == async_redact_data(
        config_entry.as_dict(), TO_REDACT
    )
    assert diagnostics_data["data"] == async_redact_data(updater.data, TO_REDACT)
    assert diagnostics_data["requests"] == async_redact_data(
        updater.client.diagnostics, TO_REDACT
    )
    assert diagnostics_data["buttons"] == ["test"]
    assert diagnostics_data["devices"] == ["wled", "ambi", "garland-2"]
    assert diagnostics_data["numbers"] == [
        "wled_blur",
        "wled_modulation_speed",
        "wled_gradient_roll",
        "wled_gradient_repeat",
        "wled_speed",
        "wled_band_count",
        "wled_color_step",
        "wled_multiplier",
        "wled_block_count",
        "wled_sensitivity",
        "wled_fade_rate",
        "wled_responsiveness",
        "wled_lows_sensitivity",
        "wled_mids_sensitivity",
        "wled_high_sensitivity",
        "wled_frequency",
        "wled_bass_threshold",
        "wled_bass_strobe_decay_rate",
        "wled_strobe_width",
        "wled_strobe_decay_rate",
        "wled_decay",
        "wled_threshold",
        "ambi_blur",
        "ambi_modulation_speed",
        "ambi_gradient_roll",
        "ambi_gradient_repeat",
        "ambi_speed",
        "ambi_band_count",
        "ambi_color_step",
        "ambi_multiplier",
        "ambi_block_count",
        "ambi_sensitivity",
        "ambi_fade_rate",
        "ambi_responsiveness",
        "ambi_lows_sensitivity",
        "ambi_mids_sensitivity",
        "ambi_high_sensitivity",
        "ambi_frequency",
        "ambi_bass_threshold",
        "ambi_bass_strobe_decay_rate",
        "ambi_strobe_width",
        "ambi_strobe_decay_rate",
        "ambi_decay",
        "ambi_threshold",
        "garland-2_blur",
        "garland-2_modulation_speed",
        "garland-2_gradient_roll",
        "garland-2_gradient_repeat",
        "garland-2_speed",
        "garland-2_band_count",
        "garland-2_color_step",
        "garland-2_multiplier",
        "garland-2_block_count",
        "garland-2_sensitivity",
        "garland-2_fade_rate",
        "garland-2_responsiveness",
        "garland-2_lows_sensitivity",
        "garland-2_mids_sensitivity",
        "garland-2_high_sensitivity",
        "garland-2_frequency",
        "garland-2_bass_threshold",
        "garland-2_bass_strobe_decay_rate",
        "garland-2_strobe_width",
        "garland-2_strobe_decay_rate",
        "garland-2_decay",
        "garland-2_threshold",
    ]
    assert diagnostics_data["selects"] == [
        "wled_background_color",
        "wled_modulation_effect",
        "wled_gradient_name",
        "wled_align",
        "wled_mode",
        "wled_ease_method",
        "wled_color",
        "wled_frequency_range",
        "wled_color_lows",
        "wled_color_mids",
        "wled_color_high",
        "wled_mixing_mode",
        "wled_lows_colour",
        "wled_mids_colour",
        "wled_high_colour",
        "wled_raindrop_animation",
        "wled_strobe_color",
        "ambi_background_color",
        "ambi_modulation_effect",
        "ambi_gradient_name",
        "ambi_align",
        "ambi_mode",
        "ambi_ease_method",
        "ambi_color",
        "ambi_frequency_range",
        "ambi_color_lows",
        "ambi_color_mids",
        "ambi_color_high",
        "ambi_mixing_mode",
        "ambi_lows_colour",
        "ambi_mids_colour",
        "ambi_high_colour",
        "ambi_raindrop_animation",
        "ambi_strobe_color",
        "garland-2_background_color",
        "garland-2_modulation_effect",
        "garland-2_gradient_name",
        "garland-2_align",
        "garland-2_mode",
        "garland-2_ease_method",
        "garland-2_color",
        "garland-2_frequency_range",
        "garland-2_color_lows",
        "garland-2_color_mids",
        "garland-2_color_high",
        "garland-2_mixing_mode",
        "garland-2_lows_colour",
        "garland-2_mids_colour",
        "garland-2_high_colour",
        "garland-2_raindrop_animation",
        "garland-2_strobe_color",
    ]
    assert diagnostics_data["sensors"] == ["fft_size", "host_api", "mic_rate"]
    assert diagnostics_data["switches"] == [
        "wled_flip",
        "wled_mirror",
        "wled_modulate",
        "wled_flip_gradient",
        "wled_color_cycler",
        "wled_sparks",
        "ambi_flip",
        "ambi_mirror",
        "ambi_modulate",
        "ambi_flip_gradient",
        "ambi_color_cycler",
        "ambi_sparks",
        "garland-2_flip",
        "garland-2_mirror",
        "garland-2_modulate",
        "garland-2_flip_gradient",
        "garland-2_color_cycler",
        "garland-2_sparks",
    ]
