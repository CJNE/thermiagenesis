import logging

from homeassistant.components.sensor import SensorStateClass
from homeassistant.helpers.entity import Entity
from pythermiagenesis.const import REGISTERS

from .const import ATTR_CLASS
from .const import ATTR_DEFAULT_ENABLED
from .const import ATTR_ICON
from .const import ATTR_LABEL
from .const import ATTR_MANUFACTURER
from .const import ATTR_STATE_CLASS
from .const import ATTR_UNIT
from .const import DOMAIN
from .const import HEATPUMP_ALARMS
from .const import HEATPUMP_ATTRIBUTES
from .const import HEATPUMP_SENSOR
from .const import SENSOR_TYPES

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

    sensors.append(ThermiaHeatpumpSensor(coordinator, HEATPUMP_SENSOR, device_info))
    for sensor in SENSOR_TYPES:
        if REGISTERS[sensor][coordinator.kind]:
            sensors.append(ThermiaGenericSensor(coordinator, sensor, device_info))
    async_add_entities(sensors, False)


class ThermiaHeatpumpSensor(Entity):
    """Define a Thermia heatpump sensor."""

    def __init__(self, coordinator, kind, device_info):
        """Initialize."""
        self._name = "Heatpump"
        # self._name = f"{coordinator.data[ATTR_MODEL]} {SENSOR_TYPES[kind][ATTR_LABEL]}"
        self._unique_id = "thermiagenesis_heatpump"
        self._device_info = device_info
        self.coordinator = coordinator
        self.kind = kind
        self._attrs = {}

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def state(self):
        """Return the state."""
        val = self.coordinator.data.get(self.kind)
        return val

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        for attr in HEATPUMP_ATTRIBUTES:
            label = (attr[0].split("_", 1)[-1]).title()
            val = self.coordinator.data.get(attr[0])
            if attr[1]:
                val = f"{val} {attr[1]}"
            self._attrs[label] = val
        if self.has_alarm():
            self._attrs["Active alarms"] = ""
        return self._attrs

    @property
    def icon(self):
        """Return the icon."""
        if self.has_alarm():
            return "mdi-alert"
        return "mdi-pulse"

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self._unique_id

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_TYPES[self.kind].get(ATTR_UNIT, None)

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
        return True

    def has_alarm(self):
        for alarm in HEATPUMP_ALARMS:
            if self.coordinator.data.get(alarm):
                return True
        return False

    def async_write_ha_state(self):
        super().async_write_ha_state()

    async def async_added_to_hass(self):
        register_attr = [self.kind]
        for attr in HEATPUMP_ATTRIBUTES:
            register_attr.append(attr[0])
        self.coordinator.registerAttribute(register_attr)
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Thermia entity."""
        await self.coordinator.async_request_refresh()


class ThermiaGenericSensor(Entity):
    """Define a Thermia generic sensor."""

    def __init__(self, coordinator, kind, device_info):
        """Initialize."""
        self._name = f"{SENSOR_TYPES[kind][ATTR_LABEL]}"
        # self._name = f"{coordinator.data[ATTR_MODEL]} {SENSOR_TYPES[kind][ATTR_LABEL]}"
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
    def state(self):
        """Return the state."""
        val = self.coordinator.data.get(self.kind)
        return val

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self):
        """Return the icon."""
        return SENSOR_TYPES[self.kind][ATTR_ICON]

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self._unique_id

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_TYPES[self.kind].get(ATTR_UNIT, None)

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return SENSOR_TYPES[self.kind].get(ATTR_CLASS, None)

    @property
    def state_class(self):
        """Return de device class of the sensor."""
        return SENSOR_TYPES[self.kind].get(
            ATTR_STATE_CLASS, SensorStateClass.MEASUREMENT
        )

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

    def async_write_ha_state(self):
        super().async_write_ha_state()

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return SENSOR_TYPES[self.kind][ATTR_DEFAULT_ENABLED]

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        """Connect to dispatcher listening for entity data notifications."""
        self.coordinator.registerAttribute(self.kind)
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Thermia entity."""
        await self.coordinator.async_request_refresh()
