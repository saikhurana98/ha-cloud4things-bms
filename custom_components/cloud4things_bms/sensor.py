from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import C4TBMSCoordinator

_LOGGER = logging.getLogger(__name__)

# keyword → (device_class, unit, state_class)
_KEY_HINTS: list[tuple[list[str], SensorDeviceClass | None, str | None, SensorStateClass]] = [
    (["kwh", "energy", "consumption", "import", "export"],
     SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
    (["kw", "power", "demand", "load"],
     SensorDeviceClass.POWER, UnitOfPower.KILO_WATT, SensorStateClass.MEASUREMENT),
    (["watt", "_w_"],
     SensorDeviceClass.POWER, UnitOfPower.WATT, SensorStateClass.MEASUREMENT),
    (["volt", "voltage", "_v_", "_v$"],
     SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT, SensorStateClass.MEASUREMENT),
    (["amp", "current", "_a_"],
     SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE, SensorStateClass.MEASUREMENT),
    (["freq", "hz"],
     SensorDeviceClass.FREQUENCY, UnitOfFrequency.HERTZ, SensorStateClass.MEASUREMENT),
    (["pf", "power_factor", "powerfactor"],
     SensorDeviceClass.POWER_FACTOR, None, SensorStateClass.MEASUREMENT),
]


def _classify(key: str) -> tuple[SensorDeviceClass | None, str | None, SensorStateClass]:
    lower = key.lower()
    for keywords, device_class, unit, state_class in _KEY_HINTS:
        if any(kw in lower for kw in keywords):
            return device_class, unit, state_class
    return None, None, SensorStateClass.MEASUREMENT


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: C4TBMSCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()

    entities = [
        C4TBMSSensor(coordinator, entry, key)
        for key in coordinator.data
    ]
    async_add_entities(entities)


class C4TBMSSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator: C4TBMSCoordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._entry = entry
        device_class, unit, state_class = _classify(key)
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_name = key.replace("_", " ").title()
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Cloud4Things",
            model="BMS Energy Monitor",
        )

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get(self._key)
