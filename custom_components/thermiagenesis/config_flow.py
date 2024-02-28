"""Adds config flow for ThermiaGenesis heat pump."""
from enum import Enum
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.const import CONF_PORT
from homeassistant.const import CONF_TYPE
from homeassistant.helpers.selector import selector
from pythermiagenesis import ThermiaConnectionError
from pythermiagenesis import ThermiaGenesis
from pythermiagenesis.const import ATTR_COIL_ENABLE_HEAT

from .const import DOMAIN  # pylint:disable=unused-import

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=""): str,
        vol.Required(CONF_PORT, default="502"): int,
        vol.Required(CONF_TYPE, default="inverter"): str,
    }
)


_LOGGER = logging.getLogger(__name__)


class ThermiaGenesisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Porsche Connect."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def _validate_input(self, data):
        """Validate the user input allows us to connect.

        Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
        """

        thermia = ThermiaGenesis(
            data[CONF_HOST],
            data[CONF_PORT],
            kind=data[CONF_TYPE],
        )
        _LOGGER.debug("Attempt connect...")
        await thermia.async_update(only_registers=[ATTR_COIL_ENABLE_HEAT])
        return {"title": data[CONF_HOST] + ":" + str(data[CONF_PORT])}

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        defaults = user_input or {CONF_HOST: "", CONF_PORT: 502, CONF_TYPE: "inverter"}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=defaults[CONF_HOST]): str,
                    vol.Required(CONF_PORT, default=defaults[CONF_PORT]): int,
                    vol.Required(CONF_TYPE, default=defaults[CONF_TYPE]): selector({
                        "select": {
                            "options": ["inverter", "mega"],
                        }
                    })
                }
            ),
            errors=self._errors,
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        self._errors = {}
        if user_input is not None:
            try:
                info = await self._validate_input(user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except ThermiaConnectionError:
                _LOGGER.info("Connect error")
                self._errors["base"] = "connection_error"
            except ValueError:
                _LOGGER.info("Value error")
                self._errors[CONF_HOST] = "wrong_host"
            except Exception as er:
                _LOGGER.info("Other error")
                _LOGGER.info(er)
                self._errors["base"] = "connection_error"

        return await self._show_config_form(user_input)


# class ThermiaGenesisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     """Handle a config flow for ThermiaGenesis heat pump."""
#
#     VERSION = 1
#     CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
#
#     def __init__(self):
#         """Initialize."""
#         self.thermia = None
#         self.host = None
#         self.port = None
#
#     async def async_step_user(self, user_input=None):
#         """Handle the initial step."""
#         errors = {}
#
#         if user_input is not None:
#             try:
#                 thermia = ThermiaGenesis(
#                     user_input[CONF_HOST],
#                     user_input[CONF_PORT],
#                     kind=user_input[CONF_TYPE],
#                 )
#                 await thermia.async_update()
#
#                 await self.async_set_unique_id("thermiagenesis")
#                 self._abort_if_unique_id_configured()
#
#                 title = f"{thermia.model}"
#                 return self.async_create_entry(title=title, data=user_input)
#             except ValueError:
#                 errors[CONF_HOST] = "wrong_host"
#             except ThermiaConnectionError:
#                 errors["base"] = "connection_error"
#
#         return self.async_show_form(
#             step_id="user", data_schema=DATA_SCHEMA, errors=errors
#         )
