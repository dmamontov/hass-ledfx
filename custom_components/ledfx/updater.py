"""LedFx data updater."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property
from typing import Any, Final

from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.number import NumberEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntityDescription
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import event
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import (
    DeviceEntryType,
    DeviceInfo,
    EntityCategory,
    EntityDescription,
)
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import utcnow
from httpx import USE_CLIENT_DEFAULT, codes

from .client import LedFxClient
from .const import (
    ATTR_DEVICE_SW_VERSION,
    ATTR_FIELD,
    ATTR_FIELD_EFFECTS,
    ATTR_FIELD_OPTIONS,
    ATTR_FIELD_TYPE,
    ATTR_LIGHT_BRIGHTNESS,
    ATTR_LIGHT_COLOR,
    ATTR_LIGHT_CONFIG,
    ATTR_LIGHT_CUSTOM_PRESETS,
    ATTR_LIGHT_DEFAULT_PRESETS,
    ATTR_LIGHT_EFFECT,
    ATTR_LIGHT_EFFECT_CONFIG,
    ATTR_LIGHT_EFFECTS,
    ATTR_LIGHT_STATE,
    ATTR_SELECT_AUDIO_INPUT,
    ATTR_SELECT_AUDIO_INPUT_OPTIONS,
    ATTR_STATE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAINTAINER,
    NAME,
    SIGNAL_NEW_BUTTON,
    SIGNAL_NEW_DEVICE,
    SIGNAL_NEW_NUMBER,
    SIGNAL_NEW_SELECT,
    SIGNAL_NEW_SENSOR,
    SIGNAL_NEW_SWITCH,
    UPDATER,
)
from .enum import ActionType, Version
from .exceptions import LedFxConnectionError, LedFxError, LedFxRequestError

PREPARE_METHODS_V1: Final = (
    "config",
    "info",
    "colors",
    "schema",
    "devices",
    "audio_devices",
    "scenes",
)

_LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-branches,too-many-lines,too-many-arguments
class LedFxUpdater(DataUpdateCoordinator):
    """LedFx data updater for interaction with LedFX API."""

    version: Version = Version.V1

    client: LedFxClient
    code: codes = codes.BAD_GATEWAY
    ip: str
    port: str

    new_button_callback: CALLBACK_TYPE | None = None
    new_device_callback: CALLBACK_TYPE | None = None
    new_number_callback: CALLBACK_TYPE | None = None
    new_select_callback: CALLBACK_TYPE | None = None
    new_sensor_callback: CALLBACK_TYPE | None = None
    new_switch_callback: CALLBACK_TYPE | None = None

    _scan_interval: int
    _is_only_check: bool = False

    def __init__(
        self,
        hass: HomeAssistant,
        ip: str,
        port: str,
        auth: Any = USE_CLIENT_DEFAULT,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        timeout: int = DEFAULT_TIMEOUT,
        is_only_check: bool = False,
    ) -> None:
        """Initialize updater.

        :rtype: object
        :param hass: HomeAssistant: Home Assistant object
        :param ip: str: ip address
        :param port: str: port
        :param auth: Any: Basic auth
        :param scan_interval: int: Update interval
        :param timeout: int: Query execution timeout
        :param is_only_check: bool: Only config flow
        """

        self.client = LedFxClient(
            get_async_client(hass, False),
            ip,
            port,
            auth,
            timeout,
        )

        self.ip = ip  # pylint: disable=invalid-name
        self.port = port

        self._scan_interval = scan_interval
        self._is_only_check = is_only_check

        if hass is not None:
            super().__init__(
                hass,
                _LOGGER,
                name=f"{NAME} updater",
                update_interval=self._update_interval,
                update_method=self.update,
            )

        self.data: dict[str, Any] = {}

        self.buttons: dict[str, LedFxEntityDescription] = {}
        self.devices: dict[str, LedFxEntityDescription] = {}
        self.numbers: dict[str, LedFxEntityDescription] = {}
        self.selects: dict[str, LedFxEntityDescription] = {}
        self.sensors: dict[str, LedFxEntityDescription] = {}
        self.switches: dict[str, LedFxEntityDescription] = {}

        self.effect_properties: dict = {}
        self.colors: dict = {}
        self.gradients: dict = {}

        self._is_first_update: bool = True

    async def async_stop(self) -> None:
        """Stop updater"""

        callbacks: list = [
            self.new_button_callback,
            self.new_device_callback,
            self.new_number_callback,
            self.new_select_callback,
            self.new_sensor_callback,
            self.new_switch_callback,
        ]

        for _callback in callbacks:
            if _callback is not None:
                _callback()  # pylint: disable=not-callable

    @cached_property
    def _update_interval(self) -> timedelta:
        """Update interval

        :return timedelta: update_interval
        """

        return timedelta(seconds=self._scan_interval)

    async def update(self) -> dict:
        """Update LedFx information.

        :return dict: dict with LedFx data.
        """

        self.code = codes.OK

        _err: LedFxError | None = None

        try:
            for method in PREPARE_METHODS_V1:
                if not self._is_only_check or method == "config":
                    await self._async_prepare(method, self.data)
        except LedFxConnectionError as _e:
            _err = _e

            self.code = codes.NOT_FOUND
        except LedFxRequestError as _e:
            _err = _e

            self.code = codes.FORBIDDEN
        else:
            if self._is_first_update:
                self._is_first_update = False

        self.data[ATTR_STATE] = codes.is_success(self.code)

        v_response: dict = await self.client.virtuals()
        self.data["paused"] = v_response["paused"]

        return self.data

    @cached_property
    def address(self) -> str:
        """Full address

        :return str
        """

        return f"{self.ip}:{self.port}"

    @property
    def device_info(self) -> DeviceInfo:
        """Device info.

        :return DeviceInfo: Service DeviceInfo.
        """

        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self.address)},
            name=NAME,
            manufacturer=MAINTAINER,
            sw_version=self.data.get(ATTR_DEVICE_SW_VERSION, None),
            configuration_url=f"http://{self.address}/",
        )

    def schedule_refresh(self, offset: timedelta) -> None:
        """Schedule refresh.

        :param offset: timedelta
        """

        if self._unsub_refresh:  # type: ignore
            self._unsub_refresh()  # type: ignore
            self._unsub_refresh = None

        self._unsub_refresh = event.async_track_point_in_utc_time(
            self.hass,
            self._job,
            utcnow().replace(microsecond=0) + offset,
        )

    async def _async_prepare(self, method: str, data: dict) -> None:
        """Prepare data.

        :param method: str
        :param data: dict
        """

        action = getattr(self, f"_async_prepare_{method}")

        if action is not None:
            await action(data)

    async def _async_prepare_info(self, data: dict) -> None:
        """Prepare info.

        :param data: dict
        """

        if self.version != Version.V1:
            return

        response: dict = await self.client.info()

        if "version" in response:
            data[ATTR_DEVICE_SW_VERSION] = response["version"]

    async def _async_prepare_colors(self, data: dict) -> None:
        """Prepare colors.

        :param data: dict
        """

        if self.version != Version.V2:
            return

        response: dict = await self.client.colors()

        colors: dict = {}
        gradients: dict = {}
        if "colors" in response:
            if "builtin" in response["colors"]:
                colors |= response["colors"]["builtin"]
            if "user" in response["colors"]:
                colors |= response["colors"]["user"]

        if "gradients" in response:
            if "builtin" in response["gradients"]:
                gradients |= response["gradients"]["builtin"]
            if "user" in response["gradients"]:
                gradients |= response["gradients"]["user"]

        self.colors = colors
        self.gradients = gradients

    async def _async_prepare_schema(self, data: dict) -> None:
        """Prepare schema.

        :param data: dict
        """

        response: dict = await self.client.schema()

        if "effects" in response and response["effects"]:
            data[ATTR_LIGHT_EFFECTS] = sorted(list(response["effects"].keys()))

            for effect, fields in response["effects"].items():
                for code, parameter in fields["schema"]["properties"].items():
                    if code == "brightness" or (
                        self.version == Version.V2 and code == "background_color"
                    ):
                        continue

                    if code in self.effect_properties:
                        if (
                            effect
                            not in self.effect_properties[code][ATTR_FIELD_EFFECTS]
                        ):
                            self.effect_properties[code][ATTR_FIELD_EFFECTS].append(
                                effect
                            )

                        continue

                    field, field_type, options = self._build_entity(code, parameter)

                    if field:
                        self.effect_properties[code] = {
                            ATTR_FIELD: field,
                            ATTR_FIELD_TYPE: field_type,
                            ATTR_FIELD_OPTIONS: options,
                            ATTR_FIELD_EFFECTS: [effect],
                        }

        if (
            "audio" in response
            and "schema" in response["audio"]
            and "properties" in response["audio"]["schema"]
            and "audio_device" in response["audio"]["schema"]["properties"]
            and "enum" in response["audio"]["schema"]["properties"]["audio_device"]
        ):
            data[ATTR_SELECT_AUDIO_INPUT_OPTIONS] = dict(
                response["audio"]["schema"]["properties"]["audio_device"]["enum"]
            )

            if (
                isinstance(data[ATTR_SELECT_AUDIO_INPUT], int)
                and str(data[ATTR_SELECT_AUDIO_INPUT])
                in data[ATTR_SELECT_AUDIO_INPUT_OPTIONS]
            ):
                data[ATTR_SELECT_AUDIO_INPUT] = data[ATTR_SELECT_AUDIO_INPUT_OPTIONS][
                    str(data[ATTR_SELECT_AUDIO_INPUT])
                ]

    def _build_entity(
        self, code: str, entity_data: dict
    ) -> tuple[EntityDescription | None, str | None, list | None]:
        """Build entity

        :param code: str: Code
        :param entity_data: dict: Entity data
        :return tuple[EntityDescription | None, str | None, list | None]
        """

        if entity_data.get("type") == "boolean":
            return (
                SwitchEntityDescription(
                    key=code,
                    name=entity_data.get("title", code.title()),
                    device_class=SwitchDeviceClass.SWITCH,
                    entity_category=EntityCategory.CONFIG,
                    entity_registry_enabled_default=False,
                ),
                "switch",
                None,
            )

        if entity_data.get("type") in ("integer", "number"):
            return (
                NumberEntityDescription(
                    key=code,
                    name=entity_data.get("title", code.title()),
                    native_max_value=float(entity_data.get("maximum", 0.0)),
                    native_min_value=float(entity_data.get("minimum", 0.0)),
                    native_step=max(float(entity_data.get("minimum", 0.1)), 0.1),
                    entity_category=EntityCategory.CONFIG,
                    entity_registry_enabled_default=False,
                ),
                "number",
                None,
            )

        if entity_data.get("type") in ("string", "color"):
            enum: list = entity_data.get("enum", [])
            field_type: str = "select"

            if entity_data.get("type") == "color":
                enum = list(
                    self.gradients.keys()
                    if entity_data.get("gradient", False)
                    else self.colors.keys()
                )
                field_type = "color"

            return (
                SelectEntityDescription(
                    key=code,
                    name=entity_data.get("title", code.title()),
                    entity_category=EntityCategory.CONFIG,
                    entity_registry_enabled_default=False,
                ),
                field_type,
                enum,
            )

        return None, None, None

    async def _async_prepare_config(self, data: dict) -> None:
        """Prepare config.

        :param data: dict
        """

        response: dict = await self.client.config()

        if "config" in response:
            await self._async_prepare_config_v1(data, response)

            return

        if "configuration_version" in response:
            self.version = Version.V2

            data[ATTR_DEVICE_SW_VERSION] = response["configuration_version"]

            await self._async_prepare_config_v2(data, response)

    async def _async_prepare_config_v1(self, data: dict, response: dict) -> None:
        """Prepare config V1.

        :param data: dict
        :param response: dict
        """

        if "audio" in response["config"]:
            for code, value in response["config"]["audio"].items():
                if code == "device_name":
                    data[ATTR_SELECT_AUDIO_INPUT] = response["config"]["audio"][
                        "device_name"
                    ]
                elif code != "device_index":
                    data[code] = value

                    if code in self.sensors:
                        continue

                    self.sensors[code] = LedFxEntityDescription(
                        description=SensorEntityDescription(
                            key=code,
                            name=code.replace("_", " ").title(),
                            state_class=SensorStateClass.TOTAL,
                            entity_category=EntityCategory.DIAGNOSTIC,
                            entity_registry_enabled_default=False,
                        ),
                        device_info=self.device_info,
                    )

                    if self.new_sensor_callback:
                        async_dispatcher_send(
                            self.hass, SIGNAL_NEW_SENSOR, self.sensors[code]
                        )

        if (
            "default_presets" in response["config"]
            and response["config"]["default_presets"]
        ):
            data[ATTR_LIGHT_DEFAULT_PRESETS] = {
                effect: sorted(list(presets.keys()))
                for effect, presets in response["config"]["default_presets"].items()
            }

        if (
            "custom_presets" in response["config"]
            and response["config"]["custom_presets"]
        ):
            data[ATTR_LIGHT_CUSTOM_PRESETS] = {
                effect: sorted(list(presets.keys()))
                for effect, presets in response["config"]["custom_presets"].items()
            }

    async def _async_prepare_config_v2(self, data: dict, response: dict) -> None:
        """Prepare config V2.

        :param data: dict
        :param response: dict
        """

        if "audio" in response:
            for code, value in response["audio"].items():
                if code == "audio_device":
                    data[ATTR_SELECT_AUDIO_INPUT] = int(
                        response["audio"]["audio_device"]
                    )
                elif code != "device_index":
                    data[code] = value

                    if code in self.sensors:
                        continue

                    self.sensors[code] = LedFxEntityDescription(
                        description=SensorEntityDescription(
                            key=code,
                            name=code.replace("_", " ").title(),
                            state_class=SensorStateClass.TOTAL,
                            entity_category=EntityCategory.DIAGNOSTIC,
                            entity_registry_enabled_default=False,
                        ),
                        device_info=self.device_info,
                    )

                    if self.new_sensor_callback:
                        async_dispatcher_send(
                            self.hass, SIGNAL_NEW_SENSOR, self.sensors[code]
                        )

        if "ledfx_presets" in response and response["ledfx_presets"]:
            data[ATTR_LIGHT_DEFAULT_PRESETS] = {
                effect: sorted(list(presets.keys()))
                for effect, presets in response["ledfx_presets"].items()
            }

        if "user_presets" in response and response["user_presets"]:
            data[ATTR_LIGHT_CUSTOM_PRESETS] = {
                effect: sorted(list(presets.keys()))
                for effect, presets in response["user_presets"].items()
            }

    async def _async_prepare_devices(self, data: dict) -> None:
        """Prepare devices.

        :param data: dict
        """

        response: dict = await self.client.devices()

        if "devices" not in response or not response["devices"]:  # pragma: no cover
            return

        if self.version == Version.V1:
            self._build_device(data, response["devices"])

            return

        v_response: dict = await self.client.virtuals()

        if "virtuals" in v_response and v_response["virtuals"]:
            devices: dict = {}
            for key, virtual in v_response["virtuals"].items():
                devices[key] = virtual

                if (
                    virtual.get("is_device")
                    and virtual.get("is_device", "") in response["devices"]
                ):
                    devices[key]["config"] |= {
                        code: value
                        for code, value in response["devices"][
                            virtual.get("is_device")
                        ]["config"].items()
                        if code == "ip_address"
                    }
                    devices[key]["type"] = response["devices"][
                        virtual.get("is_device")
                    ]["type"]

            self._build_device(data, devices)

    def _build_device(self, data: dict, devices: dict) -> None:
        """Build device

        :param data: dict
        :param devices: dict
        """

        for code, device in devices.items():
            data[f"{code}_{ATTR_LIGHT_STATE}"] = bool(
                "effect" in device and device["effect"]
            )

            if data[f"{code}_{ATTR_LIGHT_STATE}"]:
                data |= {
                    f"{code}_{ATTR_LIGHT_BRIGHTNESS}": convert_brightness(
                        float(device["effect"]["config"]["brightness"]), True
                    ),
                    f"{code}_{ATTR_LIGHT_EFFECT}": device["effect"].get("type"),
                    f"{code}_{ATTR_LIGHT_EFFECT_CONFIG}": self._convert_effect_config(
                        device["effect"]["config"]
                    ),
                }
            else:
                data |= {
                    f"{code}_{ATTR_LIGHT_BRIGHTNESS}": 0,
                    f"{code}_{ATTR_LIGHT_EFFECT}": data.get(ATTR_LIGHT_EFFECTS, ["-"])[
                        0
                    ],
                    f"{code}_{ATTR_LIGHT_EFFECT_CONFIG}": {},
                }

            if self.version == Version.V2:
                data |= {
                    f"{code}_{ATTR_LIGHT_COLOR}": device["effect"]["config"].get(
                        "background_color"
                    )
                    if data[f"{code}_{ATTR_LIGHT_STATE}"]
                    else None
                }

            data[f"{code}_{ATTR_LIGHT_CONFIG}"] = {
                config: value
                for config, value in device.get("config", {}).items()
                if config not in ["icon_name", "name"]
            }

            device_config: dict = device.get("config", {})
            device_info: DeviceInfo = DeviceInfo(
                identifiers={
                    (DOMAIN, device_config.get("ip_address", f"{self.address}-{code}"))
                },
                name=device_config.get("name", code),
                model=device_config.get("type"),
                configuration_url=f"http://{self.address}/devices/{code}",
            )

            self._prepare_device_fields(code, device_info)

            if code in self.devices:
                continue

            icon: str = device_config.get("icon_name", "")

            self.devices[code] = LedFxEntityDescription(
                description=LightEntityDescription(
                    key=code,
                    name=device_config.get("name", code),
                    icon=icon if icon.startswith("mdi:") else "mdi:led-strip-variant",
                    entity_registry_enabled_default=True,
                ),
                type=ActionType.DEVICE,
                device_info=device_info,
            )

            if self.new_device_callback:
                async_dispatcher_send(self.hass, SIGNAL_NEW_DEVICE, self.devices[code])

    def _convert_effect_config(self, config: dict) -> dict:
        """Convert effect config

        :param config: dict
        :return dict
        """

        for code, value in config.items():
            if (
                code in self.effect_properties
                and self.effect_properties[code][ATTR_FIELD_TYPE] == "color"
            ):
                colors = self.colors if value in self.colors else self.gradients
                for name, color in colors.items():
                    if color == value:
                        config[code] = name

                        break

        return config

    def _prepare_device_fields(self, code: str, device_info: DeviceInfo) -> None:
        """Prepare device fields

        :param code: str: Device code
        :param device_info: DeviceInfo: Device Info object
        """

        for prop, info in self.effect_properties.items():
            field: LedFxEntityDescription | None = None
            signal: str | None = None

            if isinstance(info[ATTR_FIELD], NumberEntityDescription):
                if f"{code}_{prop}" in self.numbers:
                    continue

                field = self.numbers[f"{code}_{prop}"] = LedFxEntityDescription(
                    description=info[ATTR_FIELD],
                    type=ActionType.DEVICE,
                    device_info=device_info,
                    device_code=code,
                    extra={
                        ATTR_FIELD_EFFECTS: sorted(info.get(ATTR_FIELD_EFFECTS, {})),
                        ATTR_FIELD_TYPE: info.get(ATTR_FIELD_TYPE),
                    },
                )

                if self.new_number_callback:
                    signal = SIGNAL_NEW_NUMBER
            elif isinstance(info[ATTR_FIELD], SwitchEntityDescription):
                if f"{code}_{prop}" in self.switches:
                    continue

                field = self.switches[f"{code}_{prop}"] = LedFxEntityDescription(
                    description=info[ATTR_FIELD],
                    type=ActionType.DEVICE,
                    device_info=device_info,
                    device_code=code,
                    extra={
                        ATTR_FIELD_EFFECTS: sorted(info.get(ATTR_FIELD_EFFECTS, {})),
                        ATTR_FIELD_TYPE: info.get(ATTR_FIELD_TYPE),
                    },
                )

                if self.new_switch_callback:
                    signal = SIGNAL_NEW_SWITCH
            elif isinstance(info[ATTR_FIELD], SelectEntityDescription):
                if f"{code}_{prop}" in self.selects:
                    continue

                field = self.selects[f"{code}_{prop}"] = LedFxEntityDescription(
                    description=info[ATTR_FIELD],
                    type=ActionType.DEVICE,
                    device_info=device_info,
                    device_code=code,
                    extra={
                        ATTR_FIELD_EFFECTS: sorted(info.get(ATTR_FIELD_EFFECTS, [])),
                        ATTR_FIELD_OPTIONS: sorted(info.get(ATTR_FIELD_OPTIONS, [])),
                        ATTR_FIELD_TYPE: info.get(ATTR_FIELD_TYPE),
                    },
                )

                if self.new_select_callback:
                    signal = SIGNAL_NEW_SELECT

            if field is not None and signal is not None:
                async_dispatcher_send(
                    self.hass,
                    signal,
                    field,
                )

    async def _async_prepare_audio_devices(self, data: dict) -> None:
        """Prepare audio_devices.

        :param data: dict
        """

        if self.version != Version.V1:
            return

        response: dict = await self.client.audio_devices()

        if "devices" in response:
            data[ATTR_SELECT_AUDIO_INPUT_OPTIONS] = dict(response["devices"])

    async def _async_prepare_scenes(self, data: dict) -> None:
        """Prepare scenes.

        :param data: dict
        """

        response: dict = await self.client.scenes()

        if "scenes" in response and response["scenes"]:
            for code, scene in response["scenes"].items():
                if code in self.buttons:
                    continue

                self.buttons[code] = LedFxEntityDescription(
                    description=ButtonEntityDescription(
                        key=code,
                        name=scene["name"].title() if "name" in scene else code,
                        icon="mdi:image",
                        entity_registry_enabled_default=True,
                    ),
                    type=ActionType.SCENE,
                    device_info=self.device_info,
                )

                if self.new_button_callback:
                    async_dispatcher_send(
                        self.hass, SIGNAL_NEW_BUTTON, self.buttons[code]
                    )


@dataclass
class LedFxEntityDescription:
    """LedFx entity description."""

    description: EntityDescription
    device_info: DeviceInfo
    device_code: str | None = None
    type: ActionType = ActionType.DEFAULT
    extra: dict | None = None


def convert_brightness(brightness: float, is_reverse: bool = False) -> float:
    """Convert brightness

    :param brightness: float
    :param is_reverse: bool
    :return: float
    """

    if is_reverse:
        return min(float(math.ceil(brightness * 100 * 2.55)), 255)

    # pylint: disable=consider-using-f-string
    return float("{:.1f}".format(min(float(brightness / 100 / 2.55), 1.0)))


@callback
def async_get_updater(hass: HomeAssistant, identifier: str) -> LedFxUpdater:
    """Return LedFxUpdater for ip address or entry id.

    :param hass: HomeAssistant
    :param identifier: str
    :return LedFxUpdater
    """

    if (
        DOMAIN not in hass.data
        or identifier not in hass.data[DOMAIN]
        or UPDATER not in hass.data[DOMAIN][identifier]
    ):
        raise ValueError(f"Integration with identifier: {identifier} not found.")

    return hass.data[DOMAIN][identifier][UPDATER]
