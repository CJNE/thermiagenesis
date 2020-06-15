"""The ThermiaGenesis component."""
import asyncio
from datetime import timedelta
import logging

from pythermiagenesis import ThermiaGenesis

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

PLATFORMS = ["sensor", "binary_sensor", "climate", "switch"]

SCAN_INTERVAL = timedelta(seconds=10)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up the ThermiaGenesis component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ThermiaGenesis from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    kind = entry.data[CONF_TYPE]

    coordinator = ThermiaGenesisDataUpdateCoordinator(hass, host=host, port=port, kind=kind)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    print(f"${DOMAIN} ${entry.entry_id}")

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
    """Class to manage fetching ThermiaGenesis data from the printer."""

    def __init__(self, hass, host, port, kind ):
        """Initialize."""
        self.thermia = ThermiaGenesis(host, port=port, kind=kind)

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.thermia.async_update()
        except (ConnectionError) as error:
            raise UpdateFailed(error)
        return self.thermia.data

    async def _async_set_data(self, register, value):
        """Set data via library."""
        try:
            await self.thermia.async_set(register, value)
        except (ConnectionError) as error:
            raise UpdateFailed(error)
        return self.thermia.data


