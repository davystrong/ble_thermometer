"""Provides the DataUpdateCoordinator."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Optional

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.active_update_coordinator import (
    ActiveBluetoothDataUpdateCoordinator,
)
from homeassistant.core import CoreState, HomeAssistant, callback
from bleak.backends.device import BLEDevice
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, DEVICE_STARTUP_TIMEOUT_SECONDS

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakError
import struct

_LOGGER = logging.getLogger(__name__)


class ThermometerCoordinator(DataUpdateCoordinator[None]):
    def __init__(
        self,
        hass: HomeAssistant,
        ble_device: BLEDevice,
    ) -> None:
        """Initialize global generic bt data updater."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN
        )
        self.ble_device = ble_device
        # self.data = {"temperature": None, "humidity": None, "voltage": None}
        self.payload = {}
        self._notify_ids = [
            "00001f1f-0000-1000-8000-00805f9b34fb"
        ]
        _LOGGER.warning("Init complete")

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        _LOGGER.warning("Setting up started")
        self.client = BleakClient(self.ble_device, timeout=30)
        await self.client.connect()
        await self.client.write_gatt_char(
            "00001f1f-0000-1000-8000-00805f9b34fb", bytearray.fromhex("33ff")
        )
        for id in self._notify_ids:
            await self.client.start_notify(
                id, self.data_callback
            )

        _LOGGER.warning("Setting up finished")

    async def _async_update_data(self):
        return self.payload

    async def data_callback(self, char, payload):
        command, *_ = struct.unpack(
            "<B", payload[:1]
        )
        self.payload[command] = payload
        _LOGGER.warning("Callback received")
        self.async_set_updated_data(self.payload)
        self.last_update_success = True
        return
        _LOGGER.warning("Callback received")
        try:
            command, voltage, temperature, humidity, count = struct.unpack(
                "<BHhHB", payload[:8]
            )
            assert command == 0x33
            _LOGGER.debug(
                f"{command}, {voltage}, {temperature}, {humidity}, {count}, {payload}"
            )
            self.data = {
                "temperature": temperature/100,
                "humidity": humidity/100,
                "voltage": voltage/1000,
                "payload": str(payload)
            }
            self.async_set_updated_data(self.data)
            self.last_update_success = True
        except struct.error as e:
            self.last_update_success = False
            _LOGGER.warning(e)
            _LOGGER.warning(payload)
        _LOGGER.warning("Callback finished")

    async def async_shutdown(self) -> None:
        for id in self._notify_ids:
            await self.client.stop_notify(id)
        await self.client.disconnect()
        await super().async_shutdown()

    @callback
    def _needs_poll(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        seconds_since_last_poll: float | None,
    ) -> bool:
        return False

    # async def _async_update(
    #     self, service_info: bluetooth.BluetoothServiceInfoBleak
    # ) -> None:
    #     """Poll the device."""
    #     await self.device.update()

    @callback
    def _async_handle_unavailable(
        self, service_info: bluetooth.BluetoothServiceInfoBleak
    ) -> None:
        """Handle the device going unavailable."""
        super()._async_handle_unavailable(service_info)
        self._was_unavailable = True

    @callback
    def _async_handle_bluetooth_event(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Handle a Bluetooth event."""
        self.ble_device = service_info.device
        _LOGGER.debug(
            f"{DOMAIN} - _async_handle_bluetooth_event - {service_info} - {self.ble_device}"
        )
        self._ready_event.set()

        if not self._was_unavailable:
            return

        self._was_unavailable = False
        # self.device.update_from_advertisement(service_info.advertisement)
        super()._async_handle_bluetooth_event(service_info, change)

    async def async_wait_ready(self) -> bool:
        """Wait for the device to be ready."""
        with contextlib.suppress(asyncio.TimeoutError):
            async with asyncio.timeout(DEVICE_STARTUP_TIMEOUT_SECONDS):
                await self._ready_event.wait()
                return True
        return False
