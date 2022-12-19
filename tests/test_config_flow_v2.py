"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines

from __future__ import annotations

import json
import logging
from typing import Final
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow, setup
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture

from custom_components.ledfx.const import (
    CONF_BASIC_AUTH,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from custom_components.ledfx.exceptions import LedFxConnectionError, LedFxRequestError
from tests.setup import MOCK_IP_ADDRESS, MOCK_PORT, OPTIONS_FLOW_DATA

OPTIONS_FLOW_EDIT_DATA: Final = {
    CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
    CONF_PORT: MOCK_PORT,
    CONF_BASIC_AUTH: False,
    CONF_TIMEOUT: 15,
    CONF_SCAN_INTERVAL: 11,
}

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""

    yield


@pytest.mark.asyncio
async def test_user(hass: HomeAssistant) -> None:
    """Test user config.

    :param hass: HomeAssistant
    """

    await setup.async_setup_component(hass, "http", {})
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_init["handler"] == DOMAIN
    assert result_init["step_id"] == "user"

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(load_fixture("config_v2_data.json"))
        )

        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {CONF_IP_ADDRESS: MOCK_IP_ADDRESS, CONF_PORT: MOCK_PORT},
        )
        await hass.async_block_till_done()

    assert result_configure["flow_id"] == result_init["flow_id"]
    assert result_configure["title"] == f"{MOCK_IP_ADDRESS}:{MOCK_PORT}"
    assert result_configure["data"][CONF_IP_ADDRESS] == MOCK_IP_ADDRESS
    assert result_configure["data"][CONF_PORT] == MOCK_PORT
    assert not result_configure["data"][CONF_BASIC_AUTH]
    assert result_configure["data"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL
    assert result_configure["data"][CONF_TIMEOUT] == DEFAULT_TIMEOUT

    assert len(mock_client.mock_calls) == 2
    assert len(mock_async_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_user_with_request_error(hass: HomeAssistant) -> None:
    """Test user config.

    :param hass: HomeAssistant
    """

    await setup.async_setup_component(hass, "http", {})
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_init["handler"] == DOMAIN
    assert result_init["step_id"] == "user"

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(side_effect=LedFxRequestError)

        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {CONF_IP_ADDRESS: MOCK_IP_ADDRESS, CONF_PORT: MOCK_PORT},
        )
        await hass.async_block_till_done()

    assert result_configure["flow_id"] == result_init["flow_id"]
    assert result_configure["step_id"] == "user"
    assert result_configure["errors"]["base"] == "request.error"

    assert len(mock_client.mock_calls) == 2
    assert len(mock_async_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
async def test_user_with_connection_error(hass: HomeAssistant) -> None:
    """Test user config.

    :param hass: HomeAssistant
    """

    await setup.async_setup_component(hass, "http", {})
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_init["handler"] == DOMAIN
    assert result_init["step_id"] == "user"

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(side_effect=LedFxConnectionError)

        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {CONF_IP_ADDRESS: MOCK_IP_ADDRESS, CONF_PORT: MOCK_PORT},
        )
        await hass.async_block_till_done()

    assert result_configure["flow_id"] == result_init["flow_id"]
    assert result_configure["step_id"] == "user"
    assert result_configure["errors"]["base"] == "connection.error"

    assert len(mock_client.mock_calls) == 2
    assert len(mock_async_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
async def test_user_with_auth_show_form(hass: HomeAssistant) -> None:
    """Test user config.

    :param hass: HomeAssistant
    """

    await setup.async_setup_component(hass, "http", {})
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_init["handler"] == DOMAIN
    assert result_init["step_id"] == "user"

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry:
        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {
                CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
                CONF_PORT: MOCK_PORT,
                CONF_BASIC_AUTH: True,
            },
        )
        await hass.async_block_till_done()

    assert result_configure["flow_id"] == result_init["flow_id"]

    assert len(mock_async_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
async def test_user_with_auth(hass: HomeAssistant) -> None:
    """Test user config.

    :param hass: HomeAssistant
    """

    await setup.async_setup_component(hass, "http", {})
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_init["handler"] == DOMAIN
    assert result_init["step_id"] == "user"

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(load_fixture("config_v2_data.json"))
        )

        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {
                CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
                CONF_PORT: MOCK_PORT,
                CONF_BASIC_AUTH: True,
            },
        )
        await hass.async_block_till_done()

        result_configure = await hass.config_entries.flow.async_configure(
            result_configure["flow_id"],
            {
                CONF_USERNAME: "test",
                CONF_PASSWORD: "test",
            },
        )
        await hass.async_block_till_done()

    assert result_configure["flow_id"] == result_init["flow_id"]
    assert result_configure["title"] == f"{MOCK_IP_ADDRESS}:{MOCK_PORT}"
    assert result_configure["data"][CONF_IP_ADDRESS] == MOCK_IP_ADDRESS
    assert result_configure["data"][CONF_PORT] == MOCK_PORT
    assert result_configure["data"][CONF_BASIC_AUTH]
    assert result_configure["data"][CONF_USERNAME] == "test"
    assert result_configure["data"][CONF_PASSWORD] == "test"
    assert result_configure["data"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL
    assert result_configure["data"][CONF_TIMEOUT] == DEFAULT_TIMEOUT

    assert len(mock_client.mock_calls) == 2
    assert len(mock_async_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_user_with_auth_revert(hass: HomeAssistant) -> None:
    """Test user config.

    :param hass: HomeAssistant
    """

    await setup.async_setup_component(hass, "http", {})
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_init["handler"] == DOMAIN
    assert result_init["step_id"] == "user"

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(load_fixture("config_v2_data.json"))
        )

        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {
                CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
                CONF_PORT: MOCK_PORT,
                CONF_BASIC_AUTH: True,
            },
        )
        await hass.async_block_till_done()

        result_configure = await hass.config_entries.flow.async_configure(
            result_configure["flow_id"],
            {
                CONF_BASIC_AUTH: False,
                CONF_USERNAME: "test",
                CONF_PASSWORD: "test",
            },
        )
        await hass.async_block_till_done()

    assert result_configure["flow_id"] == result_init["flow_id"]
    assert result_configure["title"] == f"{MOCK_IP_ADDRESS}:{MOCK_PORT}"
    assert result_configure["data"][CONF_IP_ADDRESS] == MOCK_IP_ADDRESS
    assert result_configure["data"][CONF_PORT] == MOCK_PORT
    assert not result_configure["data"][CONF_BASIC_AUTH]
    assert CONF_USERNAME not in result_configure["data"]
    assert CONF_PASSWORD not in result_configure["data"]
    assert result_configure["data"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL
    assert result_configure["data"][CONF_TIMEOUT] == DEFAULT_TIMEOUT

    assert len(mock_client.mock_calls) == 2
    assert len(mock_async_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow.

    :param hass: HomeAssistant
    """

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=OPTIONS_FLOW_DATA,
        options={},
    )
    config_entry.add_to_hass(hass)

    await setup.async_setup_component(hass, "http", {})

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(load_fixture("config_v2_data.json"))
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result_init = await hass.config_entries.options.async_init(
            config_entry.entry_id
        )

        assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result_init["step_id"] == "init"

        result_save = await hass.config_entries.options.async_configure(
            result_init["flow_id"],
            user_input=OPTIONS_FLOW_EDIT_DATA,
        )

    assert result_save["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert (
        config_entry.options[CONF_IP_ADDRESS] == OPTIONS_FLOW_EDIT_DATA[CONF_IP_ADDRESS]
    )
    assert config_entry.options[CONF_PORT] == OPTIONS_FLOW_EDIT_DATA[CONF_PORT]
    assert (
        config_entry.options[CONF_BASIC_AUTH] == OPTIONS_FLOW_EDIT_DATA[CONF_BASIC_AUTH]
    )
    assert config_entry.options[CONF_TIMEOUT] == OPTIONS_FLOW_EDIT_DATA[CONF_TIMEOUT]
    assert (
        config_entry.options[CONF_SCAN_INTERVAL]
        == OPTIONS_FLOW_EDIT_DATA[CONF_SCAN_INTERVAL]
    )
    assert len(mock_async_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_options_flow_with_auth(hass: HomeAssistant) -> None:
    """Test options flow.

    :param hass: HomeAssistant
    """

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=OPTIONS_FLOW_DATA,
        options={},
    )
    config_entry.add_to_hass(hass)

    await setup.async_setup_component(hass, "http", {})

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(
            return_value=json.loads(load_fixture("config_v2_data.json"))
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result_init = await hass.config_entries.options.async_init(
            config_entry.entry_id
        )

        assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result_init["step_id"] == "init"

        result_save = await hass.config_entries.options.async_configure(
            result_init["flow_id"],
            user_input=OPTIONS_FLOW_EDIT_DATA
            | {
                CONF_BASIC_AUTH: True,
            },
        )
        await hass.async_block_till_done()

        result_save = await hass.config_entries.options.async_configure(
            result_save["flow_id"],
            user_input=OPTIONS_FLOW_EDIT_DATA
            | {
                CONF_BASIC_AUTH: True,
                CONF_USERNAME: "test",
                CONF_PASSWORD: "test",
            },
        )
        await hass.async_block_till_done()

    assert result_save["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert (
        config_entry.options[CONF_IP_ADDRESS] == OPTIONS_FLOW_EDIT_DATA[CONF_IP_ADDRESS]
    )
    assert config_entry.options[CONF_PORT] == OPTIONS_FLOW_EDIT_DATA[CONF_PORT]
    assert config_entry.options[CONF_BASIC_AUTH]
    assert config_entry.options[CONF_USERNAME] == "test"
    assert config_entry.options[CONF_PASSWORD] == "test"
    assert config_entry.options[CONF_TIMEOUT] == OPTIONS_FLOW_EDIT_DATA[CONF_TIMEOUT]
    assert (
        config_entry.options[CONF_SCAN_INTERVAL]
        == OPTIONS_FLOW_EDIT_DATA[CONF_SCAN_INTERVAL]
    )
    assert len(mock_async_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_options_flow_request_error(hass: HomeAssistant) -> None:
    """Test options flow.

    :param hass: HomeAssistant
    """

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=OPTIONS_FLOW_DATA,
        options={},
    )
    config_entry.add_to_hass(hass)

    await setup.async_setup_component(hass, "http", {})

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(side_effect=LedFxRequestError)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result_init = await hass.config_entries.options.async_init(
            config_entry.entry_id
        )

        assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result_init["step_id"] == "init"

        result_save = await hass.config_entries.options.async_configure(
            result_init["flow_id"],
            user_input=OPTIONS_FLOW_EDIT_DATA,
        )

    assert result_save["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_save["step_id"] == "init"
    assert result_save["errors"]["base"] == "request.error"
    assert len(mock_async_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
async def test_options_flow_connection_error(hass: HomeAssistant) -> None:
    """Test options flow.

    :param hass: HomeAssistant
    """

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=OPTIONS_FLOW_DATA,
        options={},
    )
    config_entry.add_to_hass(hass)

    await setup.async_setup_component(hass, "http", {})

    with patch(
        "custom_components.ledfx.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry, patch(
        "custom_components.ledfx.updater.LedFxClient"
    ) as mock_client:
        mock_client.return_value.config = AsyncMock(side_effect=LedFxConnectionError)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result_init = await hass.config_entries.options.async_init(
            config_entry.entry_id
        )

        assert result_init["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result_init["step_id"] == "init"

        result_save = await hass.config_entries.options.async_configure(
            result_init["flow_id"],
            user_input=OPTIONS_FLOW_EDIT_DATA,
        )

    assert result_save["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result_save["step_id"] == "init"
    assert result_save["errors"]["base"] == "connection.error"
    assert len(mock_async_setup_entry.mock_calls) == 1
