from __future__ import annotations

import logging
import struct
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, Schema
from .coordinator import ThermometerCoordinator
# from .entity import ThermometerEntity
from .generic_bt_api.device import BLEThermometer

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


# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ThermometerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TemperatureSensor(coordinator),
            HumiditySensor(coordinator),
            VoltageSensor(coordinator),
            # PayloadSensor(coordinator),
        ]
    )


class ThermometerEntity(CoordinatorEntity):
    """Representation of a sensor."""

    def __init__(self, coordinator: ThermometerCoordinator):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.attrs = {}
        self._state = 0
        self._data_key = None
        self._entity_id = None

    @property
    def entity_id(self):
        """Return the entity id of the sensor."""
        if self._entity_id is not None:
            return self._entity_id
        else:
            return f"sensor.{self.coordinator.ble_device.name}_{self._data_key}".lower()
        
    @entity_id.setter
    def entity_id(self, value):
        self._entity_id = value
    
    @property
    def unique_id(self):
        return f'{dr.format_mac(self.coordinator.ble_device.address)}_{self._data_key}'

    @property
    def state(self):
        """Return the state of the sensor."""
        assert self._data_key is not None
        try:
            payload = self.coordinator.payload[0x33]
            command, voltage, temperature, humidity, count = struct.unpack(
                "<BHhHB", payload[:8]
            )
            assert command == 0x33
            _LOGGER.debug(
                f"{command}, {voltage}, {temperature}, {humidity}, {count}, {payload}"
            )
            data = {
                "temperature": temperature/100,
                "humidity": humidity/100,
                "voltage": voltage/1000,
            }
            value = data[self._data_key]
            self.attrs[self._data_key] = value
            return value
        except struct.error as e:
            _LOGGER.warning(e)
            _LOGGER.warning(payload)
        except KeyError:
            _LOGGER.warning("Not ready yet")
        

    @property
    def extra_state_attributes(self):
        return self.attrs
    
    # @callback
    # def _handle_coordinator_update(self) -> None:
    #     """Handle updated data from the coordinator."""
    #     assert self._data_key is not None
    #     value = self.coordinator.data[self._data_key]
    #     if value is not None:
    #         self._attr_native_value = value
    #         self.async_write_ha_state()

class TemperatureSensor(ThermometerEntity):
    unit_of_measurement = "°C"
    def __init__(self, coordinator: ThermometerCoordinator) -> None:
        super().__init__(coordinator)
        self._data_key = "temperature"
        self.name = 'Temperature'
        self.icon = "mdi:thermometer"


class HumiditySensor(ThermometerEntity):
    unit_of_measurement = "%"
    def __init__(self, coordinator: ThermometerCoordinator) -> None:
        super().__init__(coordinator)
        self._data_key = "humidity"
        self.name = "Humidity"
        self.icon = "mdi:water-percent"


class VoltageSensor(ThermometerEntity):
    unit_of_measurement = "V"
    def __init__(self, coordinator: ThermometerCoordinator) -> None:
        super().__init__(coordinator)
        self._data_key = "voltage"
        self.name = "Voltage"
        self.icon = "mdi:lightning-bolt"

# class PayloadSensor(ThermometerEntity):
#     unit_of_measurement = "V"
#     def __init__(self, coordinator: ThermometerCoordinator) -> None:
#         super().__init__(coordinator)
#         self._data_key = "payload"
#         self.name = "Payload"
