"""The ThermiaGenesis component."""
import asyncio
import logging
import time
from datetime import datetime
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.const import CONF_PORT
from homeassistant.const import CONF_TYPE
from homeassistant.helpers.typing import ConfigType
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from pythermiagenesis import ThermiaGenesis

from .const import DOMAIN

PLATFORMS = ["sensor", "binary_sensor", "climate", "switch", "number"]

SCAN_INTERVAL = timedelta(seconds=30)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the ThermiaGenesis component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ThermiaGenesis from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    kind = entry.data[CONF_TYPE]

    coordinator = ThermiaGenesisDataUpdateCoordinator(
        hass, host=host, port=port, kind=kind
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ThermiaGenesisDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ThermiaGenesis data from the heat pump."""

    def __init__(self, hass, host, port, kind):
        """Initialize."""
        self.thermia = ThermiaGenesis(
            host, port=port, kind=kind, delay=0.05, max_registers=1
        )
        self.kind = kind
        self.attributes = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        data = {}
        try:
            start_time = time.time()
            registers = self.attributes.keys()
            data = await self.thermia.async_update(only_registers=registers)
            # for reg in registers:
            #    #await self.thermia.async_update(only_registers=[reg]) #registers)
            #    print(f"Got {reg}: {self.thermia.data[reg]}")
            _LOGGER.debug(data)
            end_time = time.time()
            _LOGGER.debug(
                f"{datetime.now()} Fetching heatpump data took {end_time - start_time} s"
            )

        except (ConnectionError) as error:
            raise UpdateFailed(error)
        return data

    async def _async_set_data(self, register, value):
        """Set data via library."""
        try:
            await self.thermia.async_set(register, value)
        except (ConnectionError) as error:
            raise UpdateFailed(error)
        return self.thermia.data

    def registerAttribute(self, attribute):
        if type(attribute) is list:
            for name in attribute:
                _LOGGER.info(f"Register attribute for update: {name}")
                self.attributes[name] = True
        else:
            _LOGGER.info(f"Register attribute for update: {attribute}")
            self.attributes[attribute] = True

    async def wantsRefresh(self, attribute):
        await self.coordinator.async_request_refresh()
