"""Adds config flow for ThermiaGenesis Printer."""
import ipaddress
import re

from pythermiagenesis import ThermiaGenesis 
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE

from .const import DOMAIN # pylint:disable=unused-import

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=""): str,
        vol.Required(CONF_PORT, default="502"): int,
        vol.Required(CONF_TYPE, default="inverter"): str,
    }
)


def host_valid(host):
    """Return True if hostname or IP address is valid."""
    try:
        if ipaddress.ip_address(host).version == (4 or 6):
            return True
    except ValueError:
        disallowed = re.compile(r"[^a-zA-Z\d\-]")
        return all(x and not disallowed.search(x) for x in host.split("."))


class ThermiaGenesisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ThermiaGenesis heat pump."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self.thermia = None
        self.host = None
        self.port = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                if not host_valid(user_input[CONF_HOST]):
                    raise InvalidHost()

                thermia = ThermiaGenesis(user_input[CONF_HOST], user_input[CONF_PORT], kind=user_input[CONF_TYPE])
                await thermia.async_update()

                await self.async_set_unique_id("thermiagenesis")
                self._abort_if_unique_id_configured()

                title = f"{thermia.model}"
                return self.async_create_entry(title=title, data=user_input)
            except InvalidHost:
                errors[CONF_HOST] = "wrong_host"
            except ConnectionError:
                errors["base"] = "connection_error"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )



class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate that hostname/IP address is invalid."""
