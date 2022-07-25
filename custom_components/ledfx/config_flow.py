"""Configuration flows."""

from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.typing import ConfigType
from httpx import codes

from .const import (
    CONF_BASIC_AUTH,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    OPTION_IS_FROM_FLOW,
)
from .helper import async_verify_access, clean_flow_user_input

_LOGGER = logging.getLogger(__name__)


class LedFxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """First time set up flow."""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LedFxOptionsFlow:
        """Get the options flow for this handler.

        :param config_entry: config_entries.ConfigEntry: Config Entry object
        :return LedFxOptionsFlow: Options Flow object
        """

        return LedFxOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: ConfigType | None = None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user.

        :param user_input: ConfigType | None: User data
        :param errors: dict | None: Errors list
        :return FlowResult: Result object
        """

        if user_input is None:
            user_input = {}

        if errors is None:
            errors = {}

        schema: dict = {
            vol.Required(
                CONF_IP_ADDRESS, default=user_input.get(CONF_IP_ADDRESS, vol.UNDEFINED)
            ): str,
            vol.Required(
                CONF_PORT, default=user_input.get(CONF_PORT, vol.UNDEFINED)
            ): str,
            vol.Required(
                CONF_BASIC_AUTH, default=user_input.get(CONF_BASIC_AUTH, False)
            ): cv.boolean,
        }

        supports_basic_auth: bool = user_input.get(CONF_BASIC_AUTH, False)

        if supports_basic_auth and (
            not user_input.get(CONF_USERNAME, False)
            or not user_input.get(CONF_PASSWORD, False)
        ):
            schema |= {
                vol.Optional(
                    CONF_USERNAME, default=user_input.get(CONF_USERNAME, vol.UNDEFINED)
                ): str,
                vol.Optional(
                    CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, vol.UNDEFINED)
                ): str,
            }
        elif len(user_input) > 0:
            unique_id: str = f"{user_input[CONF_IP_ADDRESS]}:{user_input[CONF_PORT]}"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            code: codes = await async_verify_access(
                self.hass,
                user_input.get(CONF_IP_ADDRESS),  # type: ignore
                user_input.get(CONF_PORT),  # type: ignore
                user_input.get(CONF_USERNAME, None),
                user_input.get(CONF_PASSWORD, None),
                user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            )

            _LOGGER.debug("Verify access code: %s", code)

            if codes.is_success(code):
                return self.async_create_entry(
                    title=unique_id,
                    data=clean_flow_user_input(user_input, supports_basic_auth),
                    options={OPTION_IS_FROM_FLOW: True},
                )

            if code == codes.FORBIDDEN:
                errors["base"] = "request.error"
            else:
                errors["base"] = "connection.error"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                schema
                | {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=DEFAULT_SCAN_INTERVAL)),
                    vol.Required(
                        CONF_TIMEOUT,
                        default=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=DEFAULT_TIMEOUT)),
                }
            ),
            errors=errors,
        )


class LedFxOptionsFlow(config_entries.OptionsFlow):
    """Changing options flow."""

    _config_entry: config_entries.ConfigEntry

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow.

        :param config_entry: config_entries.ConfigEntry: Config Entry object
        """

        self._config_entry = config_entry

    async def async_step_init(self, user_input: ConfigType | None = None) -> FlowResult:
        """Manage the options.

        :param user_input: ConfigType | None: User data
        """

        if user_input is None:
            user_input = {}

        errors = {}

        schema: dict = {
            vol.Required(
                CONF_IP_ADDRESS, default=user_input.get(CONF_IP_ADDRESS, vol.UNDEFINED)
            ): str,
            vol.Required(
                CONF_PORT, default=user_input.get(CONF_PORT, vol.UNDEFINED)
            ): str,
            vol.Required(
                CONF_BASIC_AUTH, default=user_input.get(CONF_BASIC_AUTH, False)
            ): cv.boolean,
        }

        supports_basic_auth: bool = user_input.get(CONF_BASIC_AUTH, False)

        if supports_basic_auth and (
            not user_input.get(CONF_USERNAME, False)
            or not user_input.get(CONF_PASSWORD, False)
        ):
            schema |= {
                vol.Optional(
                    CONF_USERNAME, default=user_input.get(CONF_USERNAME, vol.UNDEFINED)
                ): str,
                vol.Optional(
                    CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, vol.UNDEFINED)
                ): str,
            }
        elif len(user_input) > 0:
            unique_id: str = f"{user_input[CONF_IP_ADDRESS]}:{user_input[CONF_PORT]}"

            code: codes = await async_verify_access(
                self.hass,
                user_input.get(CONF_IP_ADDRESS),  # type: ignore
                user_input.get(CONF_PORT),  # type: ignore
                user_input.get(CONF_USERNAME, None),
                user_input.get(CONF_PASSWORD, None),
                user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            )

            _LOGGER.debug("Verify access code: %s", code)

            if codes.is_success(code):
                await self.async_update_unique_id(unique_id)

                return self.async_create_entry(
                    title=unique_id,
                    data=clean_flow_user_input(user_input, supports_basic_auth),
                )

            if code == codes.FORBIDDEN:
                errors["base"] = "request.error"
            else:
                errors["base"] = "connection.error"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                schema
                | {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=DEFAULT_SCAN_INTERVAL)),
                    vol.Required(
                        CONF_TIMEOUT,
                        default=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=DEFAULT_TIMEOUT)),
                }
            ),
            errors=errors,
        )

    async def async_update_unique_id(self, unique_id: str) -> None:  # pragma: no cover
        """Async update unique_id

        :param unique_id:
        """

        if self._config_entry.unique_id == unique_id:
            return

        for flow in self.hass.config_entries.flow.async_progress(True):
            if (
                flow["flow_id"] != self.flow_id
                and flow["context"].get("unique_id") == unique_id
            ):
                self.hass.config_entries.flow.async_abort(flow["flow_id"])

        self.hass.config_entries.async_update_entry(
            self._config_entry, unique_id=unique_id
        )
