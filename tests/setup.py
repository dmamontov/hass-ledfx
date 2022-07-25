"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines

from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Final
from unittest.mock import AsyncMock

from homeassistant import setup
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture

from custom_components.ledfx.const import (
    CONF_BASIC_AUTH,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OPTION_IS_FROM_FLOW,
    UPDATER,
)
from custom_components.ledfx.helper import get_config_value
from custom_components.ledfx.updater import LedFxUpdater

MOCK_IP_ADDRESS: Final = "192.168.31.1"
MOCK_PORT: Final = "1111"
MOCK_DEVICE: Final = "wled"

OPTIONS_FLOW_DATA: Final = {
    CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
    CONF_PORT: MOCK_PORT,
    CONF_BASIC_AUTH: False,
    CONF_TIMEOUT: 10,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup(
    hass: HomeAssistant, _ip: str = MOCK_IP_ADDRESS
) -> tuple[LedFxUpdater, MockConfigEntry]:
    """Setup.

    :param hass: HomeAssistant
    :param _ip: str
    """

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=OPTIONS_FLOW_DATA | {CONF_IP_ADDRESS: _ip},
        options={OPTION_IS_FROM_FLOW: True},
    )
    config_entry.add_to_hass(hass)

    await setup.async_setup_component(hass, "http", {})

    updater: LedFxUpdater = LedFxUpdater(
        hass,
        _ip,
        get_config_value(config_entry, CONF_PORT),
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        UPDATER: updater,
    }

    return updater, config_entry


async def async_mock_client(mock_client) -> None:
    """Mock"""

    mock_client.return_value.config = AsyncMock(
        return_value=json.loads(load_fixture("config_data.json"))
    )
    mock_client.return_value.schema = AsyncMock(
        return_value=json.loads(load_fixture("schema_data.json"))
    )
    mock_client.return_value.audio_devices = AsyncMock(
        return_value=json.loads(load_fixture("audio_devices_data.json"))
    )
    mock_client.return_value.scenes = AsyncMock(
        return_value=json.loads(load_fixture("scenes_data.json"))
    )
    mock_client.return_value.devices = AsyncMock(
        return_value=json.loads(load_fixture("devices_data.json"))
    )
    mock_client.return_value.info = AsyncMock(
        return_value=json.loads(load_fixture("info_data.json"))
    )


def get_url(
    path: str,
    query_params: dict | None = None,
) -> str:
    """Generate url

    :param path: str
    :param query_params: dict | None
    :param use_stok:  bool
    :return: str
    """

    if query_params is not None and len(query_params) > 0:
        path += f"?{urllib.parse.urlencode(query_params, doseq=True)}"

    return f"http://{MOCK_IP_ADDRESS}:{MOCK_PORT}/api/{path}"


class MultipleSideEffect:  # pylint: disable=too-few-public-methods
    """Multiple side effect"""

    def __init__(self, *fns):
        """init"""

        self.funcs = iter(fns)

    def __call__(self, *args, **kwargs):
        """call"""

        func = next(self.funcs)
        return func(*args, **kwargs)
