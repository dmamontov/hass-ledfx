"""Integration helper."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.util import slugify
from httpx import USE_CLIENT_DEFAULT, codes

from .const import DEFAULT_TIMEOUT, DOMAIN
from .enum import EffectCategory
from .updater import LedFxUpdater


def get_config_value(
    config_entry: config_entries.ConfigEntry | None, param: str, default=None
) -> Any:
    """Get current value for configuration parameter.

    :param config_entry: config_entries.ConfigEntry|None: config entry from Flow
    :param param: str: parameter name for getting value
    :param default: default value for parameter, defaults to None
    :return Any: parameter value, or default value or None
    """

    return (
        config_entry.options.get(param, config_entry.data.get(param, default))
        if config_entry is not None
        else default
    )


async def async_verify_access(  # pylint: disable=too-many-arguments
    hass: HomeAssistant,
    ip: str,  # pylint: disable=invalid-name
    port: str,
    username: str | None,
    password: str | None,
    timeout: int = DEFAULT_TIMEOUT,
) -> codes:
    """Verify authentication data.

    :param hass: HomeAssistant: Home Assistant object
    :param ip: str: Ip address
    :param port: str: Port
    :param username: str | None: Basic auth username
    :param password: str | None: Basic auth password
    :param timeout: int: Timeout
    :return int: last update success
    """

    updater = LedFxUpdater(
        hass=hass,
        ip=ip,
        port=port,
        auth=build_auth(username, password),
        timeout=timeout,
        is_only_check=True,
    )

    await updater.async_request_refresh()
    await updater.async_stop()

    return updater.code


async def async_get_version(hass: HomeAssistant) -> str:
    """Get the documentation url for creating a local user.

    :param hass: HomeAssistant: Home Assistant object
    :return str: Documentation URL
    """

    integration = await async_get_integration(hass, DOMAIN)

    return f"{integration.version}"


def build_auth(username: str | None, password: str | None) -> Any:
    """Build basic auth data

    :param username: Username
    :param password: Password
    :return Any
    """

    if username is None or password is None:
        return USE_CLIENT_DEFAULT

    return (username, password)


def clean_flow_user_input(user_input: dict, supports_basic_auth: bool = False) -> dict:
    """Clean user input

    :param user_input: dict: User input
    :param supports_basic_auth: bool: Is supports basic auth
    :return dict: User input
    """

    return {
        key: value
        for key, value in user_input.items()
        if supports_basic_auth
        or (not supports_basic_auth and key not in [CONF_USERNAME, CONF_PASSWORD])
    }


def generate_entity_id(
    entity_id_format: str, ip_address: str, name: str | None = None
) -> str:
    """Generate Entity ID

    :param entity_id_format: str: Format
    :param ip_address: str: Ip address
    :param name: str | None: Name
    :return str: Entity ID
    """

    _name: str = f"_{name}" if name is not None else ""

    return entity_id_format.format(slugify(f"ledfx_{ip_address}{_name}".lower()))


def build_effects(
    effects: list, default_presets: dict[str, list], custom_presets: dict[str, list]
) -> list:
    """Build effects

    :param effects: list: Effects list
    :param default_presets: dict[str, list]: Default presets list
    :param custom_presets: dict[str, list]: Custom presets list
    :return list
    """

    full_effects: list = []

    for effect in effects:
        full_effects.append(effect)
        full_effects += [f"* {preset}" for preset in default_presets.get(effect, [])]
        full_effects += [
            f"** {preset}"
            for preset in custom_presets.get(effect, [])
            if effect in custom_presets
        ]

    return full_effects


def find_effect(
    effect: str, default_presets: dict[str, list], custom_presets: dict[str, list]
) -> tuple[str | None, str | None, EffectCategory]:
    """Find effect

    :param effect: str: Effect
    :param default_presets: dict[str, list]: Default presets list
    :param custom_presets: dict[str, list]: Custom presets list
    :return tuple[str | None, str | None, EffectCategory]
    """

    if "**" in effect:
        effect = effect.replace("** ", "")
        for code, presets in custom_presets.items():
            if effect in presets:
                return code, effect, EffectCategory.CUSTOM

    if "*" in effect:
        effect = effect.replace("* ", "")
        for code, presets in default_presets.items():
            if effect in presets:
                return code, effect, EffectCategory.DEFAULT

    return effect, None, EffectCategory.NONE
