import logging
import json

from httpx._client import USE_CLIENT_DEFAULT

from . import exceptions
from .const import (
    DOMAIN,
    BASE_RESOURCE,
    DEFAULT_TIMEOUT,
    POST_TIMEOUT
)

_LOGGER = logging.getLogger(__name__)

class LedFx(object):
    def __init__(
        self,
        httpx_client,
        ip: str,
        port: str,
        auth = USE_CLIENT_DEFAULT,
        options: dict = {}
    ) -> None:
        if ip.endswith("/"):
            ip = ip[:-1]

        self.httpx_client = httpx_client

        self.base_url = BASE_RESOURCE.format(ip = ip, port = port)
        self.auth = auth

        _LOGGER.debug("Debug LedFx: Init {}".format(self.base_url))

        self.timeout = options["timeout"] if "timeout" in options else DEFAULT_TIMEOUT

    async def get(self, path: str, is_check_status: bool = True):
        try:
            async with self.httpx_client as client:
                response = await client.get(
                    "{}/{}".format(self.base_url, path),
                    timeout = self.timeout,
                    auth = self.auth
                )

            data = json.loads(response.content)
        except Exception as e:
            _LOGGER.debug("ERROR LedFx: Connection error %r", e)
            raise exceptions.LedFxConnectionError()

        if ("status" not in data or data["status"] != "success") and is_check_status:
            _LOGGER.debug("ERROR LedFx: Connection error (success = false)")
            raise exceptions.LedFxConnectionError()

        return data

    async def post(self, path: str, data: dict, is_check_status: bool = True):
        try:
            async with self.httpx_client as client:
                response = await client.post(
                    "{}/{}".format(self.base_url, path),
                    json = data,
                    timeout = POST_TIMEOUT,
                    auth = self.auth
                )

            data = json.loads(response.content)
        except Exception as e:
            _LOGGER.debug("ERROR LedFx: Connection error %r", e)
            raise exceptions.LedFxConnectionError()

        if ("status" not in data or data["status"] != "success") and is_check_status:
            _LOGGER.debug("ERROR LedFx: Connection error (success = false)")
            raise exceptions.LedFxConnectionError()

        return data

    async def put(self, path: str, data: dict, is_check_status: bool = True):
        try:
            async with self.httpx_client as client:
                response = await client.put(
                    "{}/{}".format(self.base_url, path),
                    json = data,
                    timeout = POST_TIMEOUT,
                    auth = self.auth
                )

            data = json.loads(response.content)
        except Exception as e:
            _LOGGER.debug("ERROR LedFx: Connection error %r", e)
            raise exceptions.LedFxConnectionError()

        if ("status" not in data or data["status"] != "success") and is_check_status:
            _LOGGER.debug("ERROR LedFx: Connection error (success = false)")
            raise exceptions.LedFxConnectionError()

        return data

    async def delete(self, path: str, is_check_status: bool = True):
        try:
            async with self.httpx_client as client:
                response = await client.delete(
                    "{}/{}".format(self.base_url, path),
                    timeout = POST_TIMEOUT,
                    auth = self.auth
                )

            data = json.loads(response.content)
        except Exception as e:
            _LOGGER.debug("ERROR LedFx: Connection error %r", e)
            raise exceptions.LedFxConnectionError()

        if ("status" not in data or data["status"] != "success") and is_check_status:
            _LOGGER.debug("ERROR LedFx: Connection error (success = false)")
            raise exceptions.LedFxConnectionError()

        return data

    async def info(self) -> dict:
        return await self.get("info", False)

    async def devices(self) -> dict:
        return await self.get("devices")

    async def scenes(self) -> dict:
        return await self.get("scenes")

    async def audio_devices(self) -> dict:
        return await self.get("audio/devices", False)

    async def schema(self) -> dict:
        return await self.get("schema", False)

    async def config(self) -> dict:
        return await self.get("config", False)

    async def on(self, device: str, effect: str) -> dict:
        return await self.post("devices/{}/effects".format(device), {"config": {"active": True}, "type": effect})

    async def off(self, device: str) -> dict:
        return await self.delete("devices/{}/effects".format(device))

    async def preset(self, device: str, category: str, effect: str, preset: str) -> dict:
        return await self.put(
            "devices/{}/presets".format(device),
            {"category": category, "effect_id": effect, "preset_id": preset}
        )

    async def effect(self, device: str, effect: str, config: dict) -> dict:
        return await self.put(
            "devices/{}/effects".format(device), {"config": config, "type": effect}
        )

    async def set_audio_device(self, index: int) -> dict:
        return await self.put("audio/devices", {"index": index})

    async def run_scene(self, id: str) -> dict:
        return await self.put("scenes", {"action": "activate", "id": id})