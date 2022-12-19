"""Tests for the ledfx component."""

# pylint: disable=no-member,too-many-statements,protected-access,too-many-lines,line-too-long

from __future__ import annotations

import json
import logging

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client
from httpx import Request
from pytest_homeassistant_custom_component.common import load_fixture
from pytest_httpx import HTTPXMock

from custom_components.ledfx.client import LedFxClient
from custom_components.ledfx.enum import Method
from tests.setup import MOCK_DEVICE, MOCK_IP_ADDRESS, MOCK_PORT, get_url

_LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_info(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """info test"""

    httpx_mock.add_response(text=load_fixture("info_data.json"), method=Method.GET)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.info() == json.loads(load_fixture("info_data.json"))

    request: Request | None = httpx_mock.get_request(method=Method.GET)
    assert request is not None
    assert request.url == get_url("info")
    assert request.method == Method.GET


@pytest.mark.asyncio
async def test_devices(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """devices test"""

    httpx_mock.add_response(text=load_fixture("devices_data.json"), method=Method.GET)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.devices() == json.loads(load_fixture("devices_data.json"))

    request: Request | None = httpx_mock.get_request(method=Method.GET)
    assert request is not None
    assert request.url == get_url("devices")
    assert request.method == Method.GET


@pytest.mark.asyncio
async def test_scenes(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """scenes test"""

    httpx_mock.add_response(text=load_fixture("scenes_data.json"), method=Method.GET)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.scenes() == json.loads(load_fixture("scenes_data.json"))

    request: Request | None = httpx_mock.get_request(method=Method.GET)
    assert request is not None
    assert request.url == get_url("scenes")
    assert request.method == Method.GET


@pytest.mark.asyncio
async def test_audio_devices(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """audio devices test"""

    httpx_mock.add_response(
        text=load_fixture("audio_devices_data.json"), method=Method.GET
    )

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.audio_devices() == json.loads(
        load_fixture("audio_devices_data.json")
    )

    request: Request | None = httpx_mock.get_request(method=Method.GET)
    assert request is not None
    assert request.url == get_url("audio/devices")
    assert request.method == Method.GET


@pytest.mark.asyncio
async def test_schema(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """schema test"""

    httpx_mock.add_response(text=load_fixture("schema_data.json"), method=Method.GET)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.schema() == json.loads(load_fixture("schema_data.json"))

    request: Request | None = httpx_mock.get_request(method=Method.GET)
    assert request is not None
    assert request.url == get_url("schema")
    assert request.method == Method.GET


@pytest.mark.asyncio
async def test_config(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """config test"""

    httpx_mock.add_response(text=load_fixture("config_data.json"), method=Method.GET)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.config() == json.loads(load_fixture("config_data.json"))

    request: Request | None = httpx_mock.get_request(method=Method.GET)
    assert request is not None
    assert request.url == get_url("config")
    assert request.method == Method.GET


@pytest.mark.asyncio
async def test_device_on(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """device on test"""

    httpx_mock.add_response(
        text=load_fixture("device_on_data.json"), method=Method.POST
    )

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.device_on(MOCK_DEVICE, "wavelength(Reactive)") == json.loads(
        load_fixture("device_on_data.json")
    )

    request: Request | None = httpx_mock.get_request(method=Method.POST)
    assert request is not None
    assert request.url == get_url(f"devices/{MOCK_DEVICE}/effects")
    assert (
        request.content
        == b'{"config": {"active": true}, "type": "wavelength(Reactive)"}'
    )
    assert request.method == Method.POST


@pytest.mark.asyncio
async def test_device_off(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """device off test"""

    httpx_mock.add_response(
        text=load_fixture("device_off_data.json"), method=Method.DELETE
    )

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.device_off(MOCK_DEVICE) == json.loads(
        load_fixture("device_off_data.json")
    )

    request: Request | None = httpx_mock.get_request(method=Method.DELETE)
    assert request is not None
    assert request.url == get_url(f"devices/{MOCK_DEVICE}/effects")
    assert request.method == Method.DELETE


@pytest.mark.asyncio
async def test_preset(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """preset test"""

    httpx_mock.add_response(text=load_fixture("preset_data.json"), method=Method.PUT)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.preset(
        MOCK_DEVICE, "default_presets", "wavelength(Reactive)", "sunset-sweep"
    ) == json.loads(load_fixture("preset_data.json"))

    request: Request | None = httpx_mock.get_request(method=Method.PUT)
    assert request is not None
    assert request.url == get_url(f"devices/{MOCK_DEVICE}/presets")
    assert (
        request.content
        == b'{"category": "default_presets", "effect_id": "wavelength(Reactive)", "preset_id": "sunset-sweep"}'
    )
    assert request.method == Method.PUT


@pytest.mark.asyncio
async def test_effect(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """effect test"""

    httpx_mock.add_response(text=load_fixture("effect_data.json"), method=Method.PUT)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.effect(
        MOCK_DEVICE,
        "wavelength(Reactive)",
        {
            "blur": 8.587469069357562,
            "brightness": 1,
            "flip": True,
            "gradient_name": "Sunset",
            "gradient_roll": 4,
            "mirror": False,
            "gradient_repeat": 1,
            "background_color": "white",
        },
    ) == json.loads(load_fixture("effect_data.json"))

    request: Request | None = httpx_mock.get_request(method=Method.PUT)
    assert request is not None
    assert request.url == get_url(f"devices/{MOCK_DEVICE}/effects")
    assert (
        request.content
        == b'{"config": {"blur": 8.587469069357562, "brightness": 1, "flip": true, "gradient_name": "Sunset", "gradient_roll": 4, "mirror": false, "gradient_repeat": 1, "background_color": "white"}, "type": "wavelength(Reactive)"}'
    )
    assert request.method == Method.PUT


@pytest.mark.asyncio
async def test_set_audio_device(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """set_audio_device test"""

    httpx_mock.add_response(
        text=load_fixture("set_audio_device_data.json"), method=Method.PUT
    )

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.set_audio_device(0) == json.loads(
        load_fixture("set_audio_device_data.json")
    )

    request: Request | None = httpx_mock.get_request(method=Method.PUT)
    assert request is not None
    assert request.url == get_url("audio/devices")
    assert request.content == b'{"index": 0}'
    assert request.method == Method.PUT


@pytest.mark.asyncio
async def test_run_scene(hass: HomeAssistant, httpx_mock: HTTPXMock) -> None:
    """run_scene test"""

    httpx_mock.add_response(text=load_fixture("run_scene_data.json"), method=Method.PUT)

    client: LedFxClient = LedFxClient(
        get_async_client(hass, False), f"{MOCK_IP_ADDRESS}/", MOCK_PORT
    )

    assert await client.run_scene("test") == json.loads(
        load_fixture("run_scene_data.json")
    )

    request: Request | None = httpx_mock.get_request(method=Method.PUT)
    assert request is not None
    assert request.url == get_url("scenes")
    assert request.content == b'{"action": "activate", "id": "test"}'
    assert request.method == Method.PUT
