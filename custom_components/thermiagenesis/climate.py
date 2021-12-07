""" Thermia Genesis climate sensors."""
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_MIN_TEMP,
    ATTR_MAX_TEMP,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TARGET_TEMP_STEP,
    ATTR_CURRENT_TEMPERATURE,
    HVAC_MODE_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_OFF,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import (
  TEMP_CELSIUS,
  ATTR_TEMPERATURE,
)
from homeassistant.util.temperature import convert as convert_temperature
from .const import (
    ATTR_LABEL,
    ATTR_ICON,
    ATTR_SCALE,
    ATTR_STATUS,
    ATTR_MANUFACTURER,
    ATTR_UNIT,
    ATTR_ENABLED,
    ATTR_DEFAULT_ENABLED,
    DOMAIN,
    CLIMATE_TYPES,
    KEY_STATUS_VALUE,
    KEY_STATE_ATTRIBUTES,
)

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

    for sensor in CLIMATE_TYPES:
        sensors.append(ThermiaClimateSensor(coordinator, sensor, device_info))

    async_add_entities(sensors, False)

class ThermiaClimateSensor(ClimateEntity):
    """Define a Thermia climate sensor."""

    def __init__(self, coordinator, kind, device_info):
        """Initialize."""
        self.kind = kind
        self.meta = CLIMATE_TYPES[kind]
        self._name = f"{self.meta[ATTR_LABEL]}"
        #self._name = f"{coordinator.data[ATTR_MODEL]} {SENSOR_TYPES[kind][ATTR_LABEL]}"
        self._unique_id = f"thermiagenesis_{kind}"
        self._device_info = device_info
        self.coordinator = coordinator
        self._hvac_mode = CURRENT_HVAC_IDLE
        self._attrs = {}

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        ret = 0
        if(ATTR_TEMPERATURE in self.meta): ret = ret | SUPPORT_TARGET_TEMPERATURE
        if(ATTR_TARGET_TEMP_HIGH in self.meta and ATTR_TARGET_TEMP_LOW in self.meta): ret = ret | SUPPORT_TARGET_TEMPERATURE_RANGE
        return ret

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def current_temperature(self):
        """Return the current temperature."""
        val = self.coordinator.data.get(self.meta[ATTR_CURRENT_TEMPERATURE])
        return val

    @property
    def target_temperature_low(self):
        """Return the target low temperature."""
        if(ATTR_TEMPERATURE not in self.meta): return None
        val = self.coordinator.data.get(self.meta[ATTR_TEMPERATURE])
        return val

    @property
    def target_temperature_low(self):
        """Return the target low temperature."""
        if(ATTR_TARGET_TEMP_LOW not in self.meta): return None
        val = self.coordinator.data.get(self.meta[ATTR_TARGET_TEMP_LOW])
        return val

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return convert_temperature(
            self.meta[ATTR_MIN_TEMP], TEMP_CELSIUS, self.temperature_unit
        )

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return convert_temperature(
            self.meta[ATTR_MAX_TEMP], TEMP_CELSIUS, self.temperature_unit
        )

    @property
    def target_temperature_high(self):
        """Return the target high temperature."""
        if(ATTR_TARGET_TEMP_HIGH not in self.meta): return None
        val = self.coordinator.data.get(self.meta[ATTR_TARGET_TEMP_HIGH])
        return val

    @property
    def target_temperature_step(self):
        """Return the target temperature step."""
        if(ATTR_TARGET_TEMP_STEP not in self.meta): return 1
        val = self.meta[ATTR_TARGET_TEMP_STEP]
        return val

    @property
    def target_temperature(self):
        """Return the target temperature."""
        if(ATTR_TEMPERATURE not in self.meta): return None
        val = self.coordinator.data.get(self.meta[ATTR_TEMPERATURE])
        return val

    #@property
    #def device_state_attributes(self):
    #    """Return the state attributes."""
    #    if(KEY_STATE_ATTRIBUTES not in self.meta): return
    #    for attr in self.meta[KEY_STATE_ATTRIBUTES]:
    #        label = (attr[0].split('_', 1)[-1]).title()
    #        val = self.coordinator.data.get(attr[0])
    #        if(attr[1]): val = f"{val} {attr[1]}"
    #        self._attrs[label] = val
    #    return self._attrs

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
        return self.meta[ATTR_DEFAULT_ENABLED]

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        isEnabled = self.coordinator.data.get(self.meta[ATTR_ENABLED])
        if(not isEnabled): return CURRENT_HVAC_OFF
        val = self.coordinator.data.get(ATTR_STATUS)
        if(val == self.meta[KEY_STATUS_VALUE]): return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    @property
    def hvac_mode(self):
        isEnabled = self.coordinator.data.get(self.meta[ATTR_ENABLED])
        if(not isEnabled): return HVAC_MODE_OFF
        val = self.coordinator.data.get(ATTR_STATUS)
        if(val == self.meta[KEY_STATUS_VALUE]): return HVAC_MODE_HEAT
        return HVAC_MODE_AUTO

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_AUTO]

    async def async_set_hvac_mode(self, hvac_mode: str):
        """Set new target hvac mode."""
        print(f"Set hvac mode {hvac_mode}")
        if(hvac_mode == HVAC_MODE_OFF): 
            await self.coordinator._async_set_data(self.meta[ATTR_ENABLED], False)
        if(hvac_mode == HVAC_MODE_AUTO): 
            await self.coordinator._async_set_data(self.meta[ATTR_ENABLED], True)

    async def async_turn_on(self):
        await self.coordinator._async_set_data(self.meta[ATTR_ENABLED], True)

    async def async_turn_off(self):
        await self.coordinator._async_set_data(self.meta[ATTR_ENABLED], False)

    def async_write_ha_state(self):
        print(f"Writing state for {self.kind}: {self.state} ")
        super().async_write_ha_state()

    async def async_added_to_hass(self):
        register_attr = []
        if(ATTR_TEMPERATURE in self.meta): register_attr.append(self.meta[ATTR_TEMPERATURE])
        if(ATTR_CURRENT_TEMPERATURE in self.meta): register_attr.append(self.meta[ATTR_CURRENT_TEMPERATURE])
        if(ATTR_TARGET_TEMP_HIGH in self.meta): register_attr.append(self.meta[ATTR_TARGET_TEMP_HIGH])
        if(ATTR_TARGET_TEMP_LOW in self.meta): register_attr.append(self.meta[ATTR_TARGET_TEMP_LOW])
        if(ATTR_ENABLED in self.meta): register_attr.append(self.meta[ATTR_ENABLED])
        self.coordinator.registerAttribute(register_attr)
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Thermia entity."""
        await self.coordinator.wantsRefresh(self.kind)

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        print("Set temperature")
        print(kwargs)
        writes = {}
        if(ATTR_TARGET_TEMP_LOW in kwargs): writes[self.meta[ATTR_TARGET_TEMP_LOW]] = kwargs[ATTR_TARGET_TEMP_LOW]
        if(ATTR_TARGET_TEMP_HIGH in kwargs): writes[self.meta[ATTR_TARGET_TEMP_HIGH]] = kwargs[ATTR_TARGET_TEMP_HIGH]
        if(ATTR_TEMPERATURE in kwargs): writes[self.meta[ATTR_TEMPERATURE]] = kwargs[ATTR_TEMPERATURE]
        for i, (reg, val) in enumerate( writes.items()):
            print(f"Write {reg} value {val}")
            await self.coordinator._async_set_data(reg, val)

