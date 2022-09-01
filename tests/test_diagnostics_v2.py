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


async def test_init(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """Test init.

    :param hass: HomeAssistant
    """

    httpx_mock.add_response(
        text=load_fixture("colors_data.json"), method=Method.GET, url=get_url("colors")
    )
    httpx_mock.add_response(
        text=load_fixture("devices_v2_data.json"),
        method=Method.GET,
        url=get_url("devices"),
    )
    httpx_mock.add_response(
        text=load_fixture("scenes_data.json"), method=Method.GET, url=get_url("scenes")
    )
    httpx_mock.add_response(
        text=load_fixture("schema_v2_data.json"),
        method=Method.GET,
        url=get_url("schema"),
    )
    httpx_mock.add_response(
        text=load_fixture("config_v2_data.json"),
        method=Method.GET,
        url=get_url("config"),
    )
    httpx_mock.add_response(
        text=load_fixture("virtuals_data.json"),
        method=Method.GET,
        url=get_url("virtuals"),
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
    assert diagnostics_data["devices"] == ["wled", "wled-1"]
    assert diagnostics_data["numbers"] == [
        "wled_blur",
        "wled_background_brightness",
        "wled_modulation_speed",
        "wled_gradient_roll",
        "wled_speed",
        "wled_band_count",
        "wled_color_step",
        "wled_decay",
        "wled_multiplier",
        "wled_reactivity",
        "wled_block_count",
        "wled_sway",
        "wled_chop",
        "wled_stretch",
        "wled_sensitivity",
        "wled_gradient_repeat",
        "wled_color_shift",
        "wled_intensity",
        "wled_contrast",
        "wled_fade_rate",
        "wled_responsiveness",
        "wled_lows_sensitivity",
        "wled_mids_sensitivity",
        "wled_high_sensitivity",
        "wled_frequency",
        "wled_bass_strobe_decay_rate",
        "wled_strobe_width",
        "wled_strobe_decay_rate",
        "wled_threshold",
        "wled_strobe_decay",
        "wled_beat_decay",
        "wled-1_blur",
        "wled-1_background_brightness",
        "wled-1_modulation_speed",
        "wled-1_gradient_roll",
        "wled-1_speed",
        "wled-1_band_count",
        "wled-1_color_step",
        "wled-1_decay",
        "wled-1_multiplier",
        "wled-1_reactivity",
        "wled-1_block_count",
        "wled-1_sway",
        "wled-1_chop",
        "wled-1_stretch",
        "wled-1_sensitivity",
        "wled-1_gradient_repeat",
        "wled-1_color_shift",
        "wled-1_intensity",
        "wled-1_contrast",
        "wled-1_fade_rate",
        "wled-1_responsiveness",
        "wled-1_lows_sensitivity",
        "wled-1_mids_sensitivity",
        "wled-1_high_sensitivity",
        "wled-1_frequency",
        "wled-1_bass_strobe_decay_rate",
        "wled-1_strobe_width",
        "wled-1_strobe_decay_rate",
        "wled-1_threshold",
        "wled-1_strobe_decay",
        "wled-1_beat_decay",
    ]
    assert diagnostics_data["selects"] == [
        "wled_modulation_effect",
        "wled_gradient",
        "wled_align",
        "wled_mode",
        "wled_ease_method",
        "wled_beat_skip",
        "wled_skip_every",
        "wled_frequency_range",
        "wled_color_lows",
        "wled_color_mids",
        "wled_color_high",
        "wled_mixing_mode",
        "wled_sparks_color",
        "wled_lows_color",
        "wled_mids_color",
        "wled_high_color",
        "wled_raindrop_animation",
        "wled_strobe_color",
        "wled_color",
        "wled_strobe_frequency",
        "wled-1_modulation_effect",
        "wled-1_gradient",
        "wled-1_align",
        "wled-1_mode",
        "wled-1_ease_method",
        "wled-1_beat_skip",
        "wled-1_skip_every",
        "wled-1_frequency_range",
        "wled-1_color_lows",
        "wled-1_color_mids",
        "wled-1_color_high",
        "wled-1_mixing_mode",
        "wled-1_sparks_color",
        "wled-1_lows_color",
        "wled-1_mids_color",
        "wled-1_high_color",
        "wled-1_raindrop_animation",
        "wled-1_strobe_color",
        "wled-1_color",
        "wled-1_strobe_frequency",
    ]
    assert diagnostics_data["sensors"] == [
        "sample_rate",
        "fft_size",
        "min_volume",
        "delay_ms",
        "mic_rate",
    ]
    assert diagnostics_data["switches"] == [
        "wled_flip",
        "wled_mirror",
        "wled_modulate",
        "wled_flip_gradient",
        "wled_invert_roll",
        "wled_color_cycler",
        "wled-1_flip",
        "wled-1_mirror",
        "wled-1_modulate",
        "wled-1_flip_gradient",
        "wled-1_invert_roll",
        "wled-1_color_cycler",
    ]
