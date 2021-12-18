import logging

import asyncio
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT
)

from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send

from . import exceptions
from .const import (
    DOMAIN,
    DATA_UPDATED,
    SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    CONF_EXT_EFFECT_SETTINGS,
    CONF_EXT_SENSORS
)

from .ledfx import LedFx

from .effects import async_parse_effects
from .device import Devices, Device

from .common import (
    LedFxLight,
    LedFxSensor,
    LedFxBinarySensor,
    Scene,
    AudioInput,
    EffectSwitch,
    EffectNumber,
    EffectSelect
)

_LOGGER = logging.getLogger(__name__)

class Worker(object):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.hass = hass
        self.config_entry = config_entry

        self.api = LedFx(
            get_async_client(hass, False),
            self.ip,
            self.port,
            {"timeout": self.timeout}
        )

        self.unsub_timer = None

        self._available = False
        self.is_block = False

        self.devices = Devices()
        self._scenes = []

    @property
    def last_effect(self) -> str:
        if not self._last_effect:
            self._last_effect = self.effects[0]

        return self._last_effect

    @property
    def available(self) -> bool:
        return self._available

    @property
    def ip(self) -> str:
        return self.config_entry.options[CONF_IP_ADDRESS]

    @property
    def port(self) -> str:
        return self.config_entry.options[CONF_PORT]

    @property
    def timeout(self) -> int:
        return self.config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    @property
    def scan_interval(self) -> int:
        return self.config_entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)

    async def async_update(self) -> None:
        if self.is_block:
            return

        self.is_block = True
        devices = {}

        try:
            info = await self.api.info()
            devices = await self.api.devices()
            audio_devices = await self.api.audio_devices()
            scenes = await self.api.scenes()

            schema = await self.api.schema()
            config = await self.api.config()

            self._available = True
        except exceptions.LedFxConnectionError:
            _LOGGER.debug("ERROR LedFx connection error ({}:{})".format(self.ip, self.port))
            self._available = False

        current_devices = []
        if "devices" in devices and len(devices["devices"]) > 0:
            effects = await async_parse_effects(schema, config)

            current_devices.append(DOMAIN)

            device = Device(self.hass, self.config_entry, self.api, DOMAIN, info["version"]) \
                if not self.devices.has(DOMAIN) else self.devices.get(DOMAIN)

            await self.async_setup_general_device(device, audio_devices, config, scenes)
            
            await self.devices.async_append(device)

            for code in devices["devices"]:
                data = devices["devices"][code]

                current_devices.append(data["id"])
                device = Device(
                    self.hass,
                    self.config_entry,
                    self.api,
                    data["id"],
                    info["version"],
                    data["config"]["name"],
                    data["type"],
                    effects
                ) if not self.devices.has(data["id"]) else self.devices.get(data["id"])

                await self.async_setup_device(device, data, schema)

                await self.devices.async_append(device)


        for id in self.devices.list:
            if id not in current_devices:
                await self.devices.get(id).async_update_available(False)

        _LOGGER.debug("LedFx updated ({}:{})".format(self.ip, self.port))

        async_dispatcher_send(self.hass, DATA_UPDATED)

        self.is_block = False

    async def async_setup_device(
            self,
            device: Device,
            data: dict,
            schema: dict
    ) -> None:
        await device.async_update()
        await device.async_update_available(self._available)

        brightness = 255
        is_on = False
        if "effect" in data and len(data["effect"]) > 0:
            is_on = True
            if "brightness" in data["effect"]["config"]:
                brightness = int(data["effect"]["config"]["brightness"] * 100 * 2.55)

        await device.async_append_entity(
            LedFxLight(device, device.id, device.name),
            {
                "is_on": is_on,
                "icon": data["config"]["icon_name"] if "mdi:" in data["config"]["icon_name"] else "mdi:led-strip",
                "brightness": brightness,
                "effect": data["effect"]["type"] if "effect" in data and len(data["effect"]) > 0 else None,
            }
        )

        if "devices" in schema and len(schema["devices"]) > 0 and device.model is not None \
                and device.model in schema["devices"]:
            for property in schema["devices"][device.model]["schema"]["properties"]:
                if property in ["icon_name", "name"]:
                    continue

                if not self.config_entry.options.get(CONF_EXT_SENSORS, False):
                    if device.get_entity(property) is not None:
                        device.get_entity(property).disable()

                    continue

                prop = schema["devices"][device.model]["schema"]["properties"][property]

                if prop["type"] == "boolean":
                    entity = LedFxBinarySensor(device, property, prop["title"])
                    entity_data = {
                        "is_on": "config" in data and property in data["config"] and data["config"][property],
                    }
                else:
                    entity = LedFxSensor(device, property, prop["title"])
                    entity_data = {
                        "value": data["config"][property] if "config" in data and property in data["config"] \
                                 else None
                    }

                await device.async_append_entity(entity, entity_data)

                device.get_entity(property).enable()

        if "effects" not in schema or len(schema["effects"]) == 0:
            return effects

        for code in schema["effects"]:
            for property in schema["effects"][code]["schema"]["properties"]:
                prop = schema["effects"][code]["schema"]["properties"][property]

                device.add_effect_property(code, property, prop["default"])

                if property == "brightness":
                    continue

                if not self.config_entry.options.get(CONF_EXT_EFFECT_SETTINGS, False):
                    if device.get_entity(property) is not None:
                        device.get_entity(property).disable()

                    continue

                entity = None
                entity_data = {}
                if prop["type"] == "boolean":
                    entity = EffectSwitch(device, property, prop["title"])
                    entity_data = {
                        "is_on": is_on and property in data["effect"]["config"] \
                            and data["effect"]["config"][property],
                        "is_available": is_on,
                        "support_effects": [code]
                    }
                elif prop["type"] in ["integer", "number"]:
                    entity = EffectNumber(device, property, prop["title"])
                    entity_data = {
                        "value": float(data["effect"]["config"][property]) if is_on and property in data["effect"]["config"] \
                            else None,
                        "minimum": prop["minimum"] if "minimum" in prop else None,
                        "maximum": prop["maximum"] if "maximum" in prop else None,
                        "is_available": is_on,
                        "support_effects": [code]
                    }
                elif prop["type"] == "string":
                    entity = EffectSelect(device, property, prop["title"])
                    entity_data = {
                        "current_option": data["effect"]["config"][property] if is_on and \
                            property in data["effect"]["config"] else None,
                        "options": prop["enum"] if "enum" in prop else [],
                        "is_available": is_on,
                        "support_effects": [code]
                    }

                if is_on and property in data["effect"]["config"]:
                    device.add_effect_property(
                        code, property, data["effect"]["config"][property], True
                    )

                if entity is not None:
                    await device.async_append_entity(entity, entity_data)

                    device.get_entity(property).enable()

    async def async_setup_general_device(
            self,
            device: Device,
            audio_devices: dict,
            config: dict,
            scenes: dict
    ) -> None:
        await device.async_update()
        await device.async_update_available(self._available)

        current_scenes = []
        if "scenes" in scenes and len(scenes["scenes"]) > 0:
            for code in scenes["scenes"]:
                current_scenes.append(code)
                await device.async_append_entity(
                    Scene(device, code, scenes["scenes"][code]["name"])
                )
                device.get_entity(code).enable()

        if len(self._scenes) > 0:
            for code in self._scenes:
                if code not in current_scenes and device.get_entity(code) is not None:
                    device.get_entity(code).disable()

        self._scenes = current_scenes

        if "audio" in config["config"]:
            if "devices" in audio_devices and len(audio_devices["devices"]) > 0 \
                and "device_name" in config["config"]["audio"]:
                await device.async_append_entity(
                    AudioInput(device, "audio_input", "Audio input"),
                    {
                        "options": list(audio_devices["devices"].values()),
                        "current_option": config["config"]["audio"]["device_name"]
                    }
                )
                device.get_entity("audio_input").enable()
            elif device.get_entity("audio_input") is not None:
                device.get_entity("audio_input").disable()

            sensors = {"fft_size": "FFT size", "mic_rate": "Mic rate"}
            for code in sensors:
                if code in config["config"]["audio"]:
                    await device.async_append_entity(
                        LedFxSensor(device, code, sensors[code]),
                        {
                            "value": config["config"]["audio"][code]
                        }
                    )
                    device.get_entity(code).enable()
                elif device.get_entity(code) is not None:
                    device.get_entity(code).disable()

    async def async_setup(self) -> bool:
        _LOGGER.debug("LedFx Async setup ({}:{})".format(self.ip, self.port))

        try:
            await asyncio.sleep(1)

            await self.api.info()

            self._available = True
        except Exception as e:
            _LOGGER.debug("LedFx Incorrect config ({}:{}) %r".format(self.ip, self.port), e)
            raise ConfigEntryNotReady

        self.set_scan_interval()
        self.config_entry.add_update_listener(self.async_options_updated)

        for domain in ['light', 'sensor', 'binary_sensor', 'number', 'select', 'switch']:
            self.hass.async_create_task(
                self.hass.config_entries.async_forward_entry_setup(self.config_entry, domain)
            )

        return True

    def set_scan_interval(self) -> None:
        async def refresh(event_time):
            await self.async_update()

        if self.unsub_timer is not None:
            self.unsub_timer()

        self.unsub_timer = async_track_time_interval(
            self.hass, refresh, timedelta(seconds = self.scan_interval)
        )

    @staticmethod
    async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
        hass.data[DOMAIN][entry.entry_id].set_scan_interval()
