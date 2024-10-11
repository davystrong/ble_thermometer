"""An abstract class common to all Switchbot entities."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.bluetooth.active_update_coordinator import (
    ActiveBluetoothDataUpdateCoordinator,
)
from homeassistant.const import ATTR_CONNECTIONS
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import ToggleEntity

from bleak.backends.device import BLEDevice

from .coordinator import ThermometerCoordinator

_LOGGER = logging.getLogger(__name__)


class ThermometerEntity(ActiveBluetoothDataUpdateCoordinator[ThermometerCoordinator]):
    """Generic entity encapsulating common features of Generic BT device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: ThermometerCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._address = coordinator.ble_device.address
        self._attr_unique_id = coordinator.base_unique_id
        self._attr_device_info = {
            "connections": {(dr.CONNECTION_BLUETOOTH, self._address)},
            "name": coordinator.device_name,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        assert self._attr_name is not None
        value = self.coordinator.data[self._attr_name]
        if value is not None:
            self._attr_native_value = value
            self.async_write_ha_state()
