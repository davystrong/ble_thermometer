"""An abstract class common to all Switchbot entities."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.bluetooth.active_update_coordinator import (
    ActiveBluetoothDataUpdateCoordinator,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_CONNECTIONS
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from bleak.backends.device import BLEDevice

from .coordinator import ThermometerCoordinator

_LOGGER = logging.getLogger(__name__)

# class ThermometerEntity(CoordinatorEntity):
#     _attr_has_entity_name = True

#     def __init__(self, coordinator: ThermometerCoordinator) -> None:
#         """Initialize the entity."""
#         super().__init__(coordinator)
#         self.coordinator = coordinator
#         self._address = coordinator.ble_device.address
#         self._attr_unique_id = coordinator.base_unique_id
#         self._attr_device_info = {
#             "connections": {(dr.CONNECTION_BLUETOOTH, self._address)},
#             "name": coordinator.device_name,
#         }
#         self._data_key = None

#     @property
#     def entity_id(self):
#         """Return the entity id of the sensor."""
#         # TODO: Update this to use the id as well
#         return f"sensor.{self.coordinator.device_name}_{self._data_key}"

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Handle updated data from the coordinator."""
#         assert self._data_key is not None
#         value = self.coordinator.data[self._data_key]
#         if value is not None:
#             self._attr_native_value = value
#             self.async_write_ha_state()

