import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT
)
from homeassistant.helpers.httpx_client import get_async_client

from .core.const import (
    DOMAIN,
    SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    CONF_EXT_EFFECT_SETTINGS,
    CONF_EXT_SENSORS
)

from .core import exceptions
from .core.ledfx import LedFx

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): str,
    vol.Required(CONF_PORT): str
})

class LedFxFlowHandler(ConfigFlow, domain = DOMAIN):
    async def async_step_import(self, data: dict):
        await self.async_set_unique_id(data[CONF_IP_ADDRESS])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title = "{}:{}".format(data[CONF_IP_ADDRESS], data[CONF_PORT]), data = data)

    async def async_step_user(self, user_input = None):
        return self.async_show_form(step_id = 'auth', data_schema = AUTH_SCHEMA)

    async def async_step_auth(self, user_input):
        if user_input is None:
            return self.cur_step

        client = LedFx(get_async_client(self.hass, False), user_input[CONF_IP_ADDRESS], user_input[CONF_PORT])

        try:
            await client.info()
        except exceptions.LedFxConnectionError as e:
            return await self._prepare_error('ip_address.not_matched', e)

        entry = await self.async_set_unique_id(user_input[CONF_IP_ADDRESS])

        if entry:
            self.hass.config_entries.async_update_entry(entry, data = user_input)

            return self.async_abort(reason = 'account_updated')

        return self.async_create_entry(title = "{}:{}".format(user_input[CONF_IP_ADDRESS], user_input[CONF_PORT]), data = user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return OptionsFlowHandler(config_entry)

    async def _prepare_error(self, code: str, err):
        _LOGGER.error("Error setting up LedFx API: %r", err)

        return self.async_show_form(
            step_id = 'auth',
            data_schema = AUTH_SCHEMA,
            errors = {'base': code}
        )

class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input = None):
        return await self.async_step_settings()

    async def async_step_settings(self, user_input = None):
        options_schema = vol.Schema({
            vol.Required(CONF_IP_ADDRESS, default = self.config_entry.options.get(CONF_IP_ADDRESS, "")): str,
            vol.Required(CONF_PORT, default = self.config_entry.options.get(CONF_PORT, "")): str,
            vol.Optional(
                CONF_EXT_EFFECT_SETTINGS,
                default=self.config_entry.options.get(CONF_EXT_EFFECT_SETTINGS, False)
            ): cv.boolean,
            vol.Optional(
                CONF_EXT_SENSORS,
                default=self.config_entry.options.get(CONF_EXT_SENSORS, False)
            ): cv.boolean,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default = self.config_entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
            ): cv.positive_int,
            vol.Optional(
                CONF_TIMEOUT,
                default = self.config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
            ): cv.positive_int
        })

        if user_input:
            client = LedFx(get_async_client(self.hass, False), user_input[CONF_IP_ADDRESS], user_input[CONF_PORT])

            try:
                await client.info()
            except exceptions.LedFxConnectionError as e:
                return await self._prepare_error('ip_address.not_matched', e, options_schema)

            return self.async_create_entry(title = '', data = user_input)

        return self.async_show_form(step_id = "settings", data_schema = options_schema)

    async def _prepare_error(self, code: str, err, options_schema):
        _LOGGER.error("Error setting up LedFx API: %r", err)

        return self.async_show_form(
            step_id = 'settings',
            data_schema = options_schema,
            errors = {'base': code}
        )
