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

from .const import DOMAIN, DEVICE_STARTUP_TIMEOUT_SECONDS

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakError
import struct

_LOGGER = logging.getLogger(__name__)


class ThermometerCoordinator(ActiveBluetoothDataUpdateCoordinator[None]):
    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        ble_device: BLEDevice,
        device_name: str,
        base_unique_id: str,
        connectable: bool,
    ) -> None:
        """Initialize global generic bt data updater."""
        super().__init__(
            hass=hass,
            logger=logger,
            address=ble_device.address,
            needs_poll_method=self._needs_poll,
            # poll_method=self._async_update,
            mode=bluetooth.BluetoothScanningMode.ACTIVE,
            connectable=connectable,
        )
        self.ble_device = ble_device
        self.device_name = device_name
        self.base_unique_id = base_unique_id
        self._ready_event = asyncio.Event()
        self._was_unavailable = True
        self._client: BleakClient
        self.data = {"temperature": None, "humidity": None, "voltage": None}

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        self._client = BleakClient(self.ble_device, timeout=30)
        await self._client.connect()
        await self._client.write_gatt_char(
            "00001f1f-0000-1000-8000-00805f9b34fb", bytearray.fromhex("33ff")
        )
        await self._client.start_notify(
            "00001f1f-0000-1000-8000-00805f9b34fb", self.therm_data_callback
        )

    async def therm_data_callback(self, char, payload):
        try:
            command, voltage, temperature, humidity, count = struct.unpack(
                "<BHhHB", payload[:10]
            )
            assert command == 0x33
            _LOGGER.debug(
                f"{command}, {voltage}, {temperature}, {humidity}, {count}, {payload}"
            )
            self.data = {
                "temperature": temperature,
                "humidity": humidity,
                "voltage": voltage,
            }
        except struct.error:
            pass

    async def async_shutdown(self) -> None:
        await self._client.stop_notify("00001f1f-0000-1000-8000-00805f9b34fb")
        await self._client.disconnect()
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
        self.device.update_from_advertisement(service_info.advertisement)
        super()._async_handle_bluetooth_event(service_info, change)

    async def async_wait_ready(self) -> bool:
        """Wait for the device to be ready."""
        with contextlib.suppress(asyncio.TimeoutError):
            async with asyncio.timeout(DEVICE_STARTUP_TIMEOUT_SECONDS):
                await self._ready_event.wait()
                return True
        return False
