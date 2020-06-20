import logging

from homeassistant.components.switch import SwitchEntity
from pythermiagenesis.const import REGISTERS

from .const import (
    ATTR_LABEL,
    ATTR_ICON,
    ATTR_SCALE,
    ATTR_CLASS,
    ATTR_MANUFACTURER,
    ATTR_UNIT,
    ATTR_DEFAULT_ENABLED,
    DOMAIN,
    SWITCH_TYPES,
    HEATPUMP_ATTRIBUTES,
    HEATPUMP_ALARMS,
)

ATTR_COUNTER = "counter"
ATTR_FIRMWARE = "firmware"
ATTR_MODEL = "Diplomat Inverter Duo"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add Thermia entities from a config_entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = []

    device_info = {
        "identifiers": {(DOMAIN, ATTR_MODEL)},
        "name": ATTR_MODEL,
        "manufacturer": ATTR_MANUFACTURER,
        "model": ATTR_MODEL,
        "sw_version": coordinator.data.get(ATTR_FIRMWARE),
    }

    for sensor in SWITCH_TYPES:
        if REGISTERS[sensor][coordinator.kind]:
            sensors.append(ThermiaSwitch(coordinator, sensor, device_info))
    async_add_entities(sensors, False)

class ThermiaSwitch(SwitchEntity):
    """Define a Thermia generic switch."""

    def __init__(self, coordinator, kind, device_info):
        """Initialize."""
        self._name = f"{SWITCH_TYPES[kind][ATTR_LABEL]}"
        #self._name = f"{coordinator.data[ATTR_MODEL]} {SENSOR_TYPES[kind][ATTR_LABEL]}"
        self._unique_id = f"thermiagenesis_{kind}"
        self._device_info = device_info
        self.coordinator = coordinator
        self.kind = kind
        self._attrs = {}

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def is_on(self):
        """Return the state."""
        val = self.coordinator.data.get(self.kind)
        return val

    @property
    def device_class(self):
        """Return the device class."""
        if(ATTR_CLASS not in SWITCH_TYPES[self.kind]): return None
        return SWITCH_TYPES[self.kind][ATTR_CLASS]

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self._unique_id

    @property
    def available(self):
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def device_info(self):
        """Return the device info."""
        return self._device_info

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return SWITCH_TYPES[self.kind][ATTR_DEFAULT_ENABLED]

    def async_write_ha_state(self):
        print(f"Writing state for {self.kind}: {self.state} ")
        super().async_write_ha_state()

    async def async_added_to_hass(self):
        self.coordinator.registerAttribute(self.kind)
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Thermia entity."""
        await self.coordinator.wantsRefresh(self.kind)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.coordinator._async_set_data(self.kind, True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        await self.coordinator._async_set_data(self.kind, False)

