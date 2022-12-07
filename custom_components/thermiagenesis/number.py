import logging

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.components.number import NumberEntity
from homeassistant.const import PERCENTAGE
from homeassistant.const import TEMP_CELSIUS

from homeassistant.helpers.entity import Entity
from pythermiagenesis.const import REGISTERS

from .const import ATTR_CLASS
from .const import ATTR_DEFAULT_ENABLED
from .const import ATTR_ICON
from .const import ATTR_LABEL
from .const import ATTR_MANUFACTURER
from .const import ATTR_STATE_CLASS
from .const import ATTR_UNIT
from .const import ATTR_MIN_VALUE
from .const import ATTR_MAX_VALUE
from .const import DOMAIN
from .const import HEATPUMP_ALARMS
from .const import HEATPUMP_ATTRIBUTES
from .const import HEATPUMP_SENSOR
from .const import NUMBER_TYPES

ATTR_COUNTER = "counter"
ATTR_FIRMWARE = "firmware"
ATTR_MODEL = "Diplomat Inverter Duo"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add Thermia entities from a config_entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    numbers = []

    device_info = {
        "identifiers": {(DOMAIN, ATTR_MODEL)},
        "name": ATTR_MODEL,
        "manufacturer": ATTR_MANUFACTURER,
        "model": ATTR_MODEL,
        "sw_version": coordinator.data.get(ATTR_FIRMWARE),
    }

    for number in NUMBER_TYPES:
        if REGISTERS[number][coordinator.kind]:
            numbers.append(ThermiaGenericNumber(coordinator, number, device_info))
    async_add_entities(numbers, False)


def range_for_unit(unit):
    if unit == PERCENTAGE:
        return [0, 100]
    if unit == TEMP_CELSIUS:
        return [-40, 100]
    return [0, 100]


class ThermiaGenericNumber(NumberEntity):
    """Define a Thermia generic sensor."""

    def __init__(self, coordinator, kind, device_info):
        """Initialize."""
        self._name = f"{NUMBER_TYPES[kind][ATTR_LABEL]}"
        # self._name = f"{coordinator.data[ATTR_MODEL]} {SENSOR_TYPES[kind][ATTR_LABEL]}"
        self._unique_id = f"thermiagenesis_{kind}"
        self._device_info = device_info
        self.coordinator = coordinator
        self.kind = kind
        meta = NUMBER_TYPES[kind]
        range = range_for_unit(meta.get(ATTR_UNIT, None))
        self.min = meta.get(ATTR_MIN_VALUE, range[0])
        self.max = meta.get(ATTR_MAX_VALUE, range[1])
        self._attrs = {}

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.kind)

    @property
    def native_min_value(self):
        """Return the state of the sensor."""
        return self.min

    @property
    def native_max_value(self):
        """Return the state of the sensor."""
        return self.max

    @property
    def native_step(self):
        """Return the state of the sensor."""
        return 1

    async def async_set_native_value(self, value: float) -> None:
        """Change the selected option."""
        _LOGGER.info("Writing holding register %s value %s", self.kind, value)
        await self.coordinator._async_set_data(self.kind, value)
        _LOGGER.debug("Done writing")
        self.async_schedule_update_ha_state()

    @property
    def native_unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return NUMBER_TYPES[self.kind].get(ATTR_UNIT, None)

    @property
    def icon(self):
        """Return the icon."""
        return NUMBER_TYPES[self.kind][ATTR_ICON]

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self._unique_id

    @property
    def device_info(self):
        """Return the device info."""
        return self._device_info

    def async_write_ha_state(self):
        super().async_write_ha_state()

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return NUMBER_TYPES[self.kind][ATTR_DEFAULT_ENABLED]

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
