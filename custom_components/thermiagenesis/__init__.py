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
from pythermiagenesis.const import ATTR_INPUT_SOFTWARE_VERSION_MAJOR
from pythermiagenesis.const import ATTR_INPUT_SOFTWARE_VERSION_MICRO
from pythermiagenesis.const import ATTR_INPUT_SOFTWARE_VERSION_MINOR

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
    # Request the software version registers before the first refresh. The
    # coordinator only reads registers that entities have registered, and no
    # entity exists yet -- so without this the first refresh asks for nothing
    # and no firmware version is available for the device_info the platforms
    # build a moment later.
    coordinator.registerAttribute(
        [
            ATTR_INPUT_SOFTWARE_VERSION_MAJOR,
            ATTR_INPUT_SOFTWARE_VERSION_MINOR,
            ATTR_INPUT_SOFTWARE_VERSION_MICRO,
        ]
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Refresh again now that the platforms have registered everything they
    # want. Entities are added with async_add_entities(..., False), so without
    # this every entity reports "unknown" until the next scheduled poll -- up
    # to SCAN_INTERVAL seconds after each setup or reload.
    await coordinator.async_refresh()

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
            host, port=port, kind=kind, delay=0.05, max_registers=16
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

    @property
    def firmware(self):
        """Return the pump firmware version, or None if not yet read.

        Computed here rather than read from ThermiaGenesis.firmware: the
        library sets that attribute from self.data *before* overwriting
        self.data with the freshly read values, so it lags one refresh behind
        and is still None when device_info is built.
        """
        data = self.data or {}
        try:
            return (
                f"{data[ATTR_INPUT_SOFTWARE_VERSION_MAJOR]}"
                f".{data[ATTR_INPUT_SOFTWARE_VERSION_MINOR]}"
                f".{data[ATTR_INPUT_SOFTWARE_VERSION_MICRO]}"
            )
        except KeyError:
            return None

    def registerAttribute(self, attribute):
        if type(attribute) is list:
            for name in attribute:
                _LOGGER.debug(f"Register attribute for update: {name}")
                self.attributes[name] = True
        else:
            _LOGGER.debug(f"Register attribute for update: {attribute}")
            self.attributes[attribute] = True

    async def wantsRefresh(self, attribute):
        await self.coordinator.async_request_refresh()
