"""Support for Generic BT binary sensor."""
from __future__ import annotations

import logging
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
from .entity import ThermometerEntity
from .generic_bt_api.device import BLEThermometer


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
        ]
    )

    # platform = entity_platform.async_get_current_platform()
    # platform.async_register_entity_service(
    #     "write_gatt", Schema.WRITE_GATT.value, "write_gatt"
    # )
    # platform.async_register_entity_service(
    #     "read_gatt", Schema.READ_GATT.value, "read_gatt"
    # )


class TemperatureSensor(ThermometerEntity, SensorEntity):
    _attr_name = "temperature"


class HumiditySensor(ThermometerEntity, SensorEntity):
    _attr_name = "humidity"


class VoltageSensor(ThermometerEntity, SensorEntity):
    _attr_name = "voltage"
