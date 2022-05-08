"""ThermiaGenesisEntity class"""
import logging

from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_MANUFACTURER
from .const import DOMAIN

ATTR_MODEL = "Diplomat Inverter Duo"
ATTR_FIRMWARE = "firmware"

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ThermiaGenesisEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry, kind, meta=None):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.config_entry = config_entry
        if meta is None:
            self.meta = {"attrs": {}}
        else:
            self.meta = meta
            if self.meta.get("category", None) is not None:
                self.meta["category"] = EntityCategory(self.meta["category"])

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, ATTR_MODEL)},
            "name": ATTR_MODEL,
            "manufacturer": ATTR_MANUFACTURER,
            "model": ATTR_MODEL,
            "sw_version": self.coordinator.data.get(ATTR_FIRMWARE),
        }

    @property
    def entity_category(self):
        return self.meta.get("category", None)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {
            "integration": DOMAIN,
        }
        return {**attrs, **self.meta["attrs"]}


class HeatpumpEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry, kind, meta=None):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.coordinator = coordinator
        if meta is None:
            self.meta = {"attrs": {}}
        else:
            self.meta = meta
        if meta is not None:
            if self.meta.get("category", None) is not None:
                self.meta["category"] = EntityCategory(self.meta["category"])

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, ATTR_MODEL)},
            "name": ATTR_MODEL,
            "manufacturer": ATTR_MANUFACTURER,
            "model": ATTR_MODEL,
            "sw_version": self.coordinator.data.get(ATTR_FIRMWARE),
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {
            "integration": DOMAIN,
        }
        return {**attrs, **self.meta["attrs"]}

    @property
    def entity_category(self):
        return self.meta.get("category", None)
