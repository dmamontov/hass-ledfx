DOMAIN = "ledfx"

BASE_RESOURCE = "http://{ip}:{port}/api"
DEFAULT_MANUFACTURER = "LedFx"

DATA_UPDATED = "ledfx_data_updated"

CONF_EXT_EFFECT_SETTINGS = "ext_effect_settings"
CONF_EXT_SENSORS = "ext_sensors"

SCAN_INTERVAL = 10
DEFAULT_TIMEOUT = 5
POST_TIMEOUT = 60

ICONS = {
    "audio_input": "mdi:audio-input-rca",

    "color_cycler": "mdi:palette",
    "flip": "mdi:flip-horizontal",
    "flip_gradient": "mdi:gradient-horizontal",
    "mirror": "mdi:mirror",
    "modulate": "mdi:view-module-outline",
    "sparks": "mdi:shimmer",

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

    "center_offset": "mdi:debug-step-over",
    "channel_offset": "mdi:debug-step-over",
    "e131_packet_priority": "mdi:priority-high",
    "force_refresh": "mdi:refresh",
    "ip_address": "mdi:map-marker",
    "max_brightness": "mdi:brightness-7",
    "pixel_count": "mdi:counter",
    "preview_only": "mdi:eye",
    "refresh_rate": "mdi:refresh",
    "universe": "mdi:earth",
    "universe_size": "mdi:earth-plus",

    "fft_size": "mdi:numeric",
    "mic_rate": "mdi:volume-high",
}