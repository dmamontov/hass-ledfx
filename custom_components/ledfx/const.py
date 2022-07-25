"""General constants."""
from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

# fmt: off
DOMAIN: Final = "ledfx"
NAME: Final = "LedFx"
MAINTAINER: Final = "LedFx Developers"
ATTRIBUTION: Final = "Data provided by LedFx"

PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.LIGHT,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]

"""Diagnostic const"""
DIAGNOSTIC_DATE_TIME: Final = "date_time"
DIAGNOSTIC_MESSAGE: Final = "message"
DIAGNOSTIC_CONTENT: Final = "content"

"""Helper const"""
UPDATER: Final = "updater"
UPDATE_LISTENER: Final = "update_listener"
SIGNAL_NEW_BUTTON: Final = f"{DOMAIN}-new-button"
SIGNAL_NEW_DEVICE: Final = f"{DOMAIN}-new-device"
SIGNAL_NEW_NUMBER: Final = f"{DOMAIN}-new-number"
SIGNAL_NEW_SELECT: Final = f"{DOMAIN}-new-select"
SIGNAL_NEW_SENSOR: Final = f"{DOMAIN}-new-sensor"
SIGNAL_NEW_SWITCH: Final = f"{DOMAIN}-new-switch"
OPTION_IS_FROM_FLOW: Final = "is_from_flow"

"""Custom conf"""
CONF_BASIC_AUTH: Final = "basic_auth"

"""Default settings"""
DEFAULT_SCAN_INTERVAL: Final = 7
DEFAULT_TIMEOUT: Final = 10
DEFAULT_POST_TIMEOUT: Final = 60
DEFAULT_CALL_DELAY: Final = 1
DEFAULT_SLEEP: Final = 3

"""LedFx API client const"""
CLIENT_URL: Final = "http://{ip}:{port}/api"

"""Attributes"""
ATTR_STATE: Final = "state"
ATTR_STATE_NAME: Final = "State"
ATTR_DEVICE: Final = "device"
ATTR_DEVICE_SW_VERSION: Final = "device_sw_version"
ATTR_FIELD: Final = "field"
ATTR_FIELD_EFFECTS: Final = "effects"
ATTR_FIELD_OPTIONS: Final = "options"

"""Select attributes"""
ATTR_SELECT_AUDIO_INPUT: Final = "audio_input"
ATTR_SELECT_AUDIO_INPUT_NAME: Final = "Audio input"
ATTR_SELECT_AUDIO_INPUT_OPTIONS: Final = "audio_input_options"

"""Light attributes"""
ATTR_LIGHT_STATE: Final = "state"
ATTR_LIGHT_BRIGHTNESS: Final = "brightness"
ATTR_LIGHT_CONFIG: Final = "config"
ATTR_LIGHT_EFFECT: Final = "effect"
ATTR_LIGHT_EFFECT_CONFIG: Final = "effect_config"
ATTR_LIGHT_EFFECTS: Final = "effects"
ATTR_LIGHT_DEFAULT_PRESETS: Final = "default_presets"
ATTR_LIGHT_CUSTOM_PRESETS: Final = "custom_presets"

"""Icons"""
SENSOR_ICONS: Final = {
    "fft_size": "mdi:numeric",
    "mic_rate": "mdi:microphone-settings",
    "host_api": "mdi:api",
}

SELECT_ICONS: Final = {
    "align": "mdi:format-vertical-align-center",
    "background_color": "mdi:format-color-fill",
    "color": "mdi:format-color-fill",
    "color_high": "mdi:format-color-fill",
    "color_lows": "mdi:format-color-fill",
    "color_mids": "mdi:format-color-fill",
    "ease_method": "mdi:fence",
    "frequency": "mdi:sine-wave",
    "frequency_range": "mdi:sine-wave",
    "gradient_name": "mdi:gradient-horizontal",
    "high_colour": "mdi:format-color-fill",
    "lows_colour": "mdi:format-color-fill",
    "mids_colour": "mdi:format-color-fill",
    "mixing_mode": "mdi:bowl-mix",
    "mode": "mdi:book-open",
    "modulation_effect": "mdi:auto-fix",
    "raindrop_animation": "mdi:transition",
    "strobe_color": "mdi:format-color-fill",
}

NUMBER_ICONS: Final = {
    "band_count": "mdi:counter",
    "bass_strobe_decay_rate": "mdi:volume-vibrate",
    "bass_threshold": "mdi:volume-vibrate",
    "block_count": "mdi:counter",
    "blur": "mdi:blur",
    "color_step": "mdi:debug-step-over",
    "decay": "mdi:close-box-multiple-outline",
    "fade_rate": "mdi:reiterate",
    "gradient_repeat": "mdi:repeat-variant",
    "gradient_roll": "mdi:script-outline",
    "high_sensitivity": "mdi:brightness-7",
    "lows_sensitivity": "mdi:brightness-7",
    "mids_sensitivity": "mdi:brightness-7",
    "modulation_speed": "mdi:speedometer",
    "multiplier": "mdi:aspect-ratio",
    "responsiveness": "mdi:brightness-7",
    "sensitivity": "mdi:brightness-7",
    "speed": "mdi:speedometer",
    "strobe_decay_rate": "mdi:reiterate",
    "strobe_width": "mdi:table-column-width",
    "threshold": "mdi:debug-step-over",
}

SWITCH_ICONS: Final = {
    "color_cycler": "mdi:palette",
    "flip": "mdi:flip-horizontal",
    "flip_gradient": "mdi:gradient-horizontal",
    "mirror": "mdi:mirror",
    "modulate": "mdi:view-module-outline",
    "sparks": "mdi:shimmer",
}
