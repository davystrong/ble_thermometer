import asyncio
import struct

from bleak import BleakClient, BleakScanner


def data_callback(char, payload):
    try:
        command, voltage, temperature, humidity, count, something = struct.unpack(
            "<BHhHBH", payload[:10]
        )
        assert command == 0x33
        print(command, voltage, temperature, humidity, count, something, payload)
    except struct.error:
        pass


async def main():
    """Set up Generic BT from a config entry."""
    # address: str = "A4:C1:38:90:FA:0E"
    address: str = "6DD66462-DDFA-E597-F9FD-E639532980C3"
    devices = await BleakScanner.discover(timeout=10)
    print(devices)
    device = next(dev for dev in devices if dev.address == address)
    # print(devices)
    async with BleakClient(device, timeout=5) as client:
        await client.write_gatt_char(
            "00001f1f-0000-1000-8000-00805f9b34fb", bytearray.fromhex("33ff")
        )
        await client.start_notify("00001f1f-0000-1000-8000-00805f9b34fb", data_callback)
        await asyncio.sleep(500.0)
        await client.stop_notify("00001f1f-0000-1000-8000-00805f9b34fb")
        # id = int.from_bytes(payload[0:1], byteorder="little", signed=False)
        # battery = int.from_bytes(payload[1:3], byteorder="little", signed=False)
        # temperature = int.from_bytes(payload[3:5], byteorder="little", signed=True)
        # humidity = int.from_bytes(payload[5:7], byteorder="little", signed=False)
        # services = await client.get_services()
        # print(services)
        # temp_bytes = await client.read_gatt_char("00002a6e-0000-1000-8000-00805f9b34fb")
        # print(int.from_bytes(temp_bytes, byteorder="little", signed=True))
        # hum_bytes = await client.read_gatt_char("00002a6f-0000-1000-8000-00805f9b34fb")
        # print(int.from_bytes(hum_bytes, byteorder="little", signed=True))
        # payload_bytes = await client.read_gatt_char(
        #     "00001f1f-0000-1000-8000-00805f9b34fb"
        # )
        # print(payload_bytes)
        # print(int.from_bytes(payload_bytes[:2], byteorder="little", signed=True))
        # print(int.from_bytes(payload_bytes[2:4], byteorder="little", signed=True))
        # print(int.from_bytes(payload_bytes[4:5], byteorder="little", signed=True))
        # print(int.from_bytes(payload_bytes[5:7], byteorder="little", signed=True))
        # print(int.from_bytes(payload_bytes[7:9], byteorder="little", signed=True))
    # byte_data = await device.read_gatt_char('00002a6e-0000-1000-8000-00805f9b34fb')
    # print(int(byte_data))

    # coordinator = hass.data[DOMAIN][entry.entry_id] = ThermometerCoordinator(hass, _LOGGER, ble_device, device, entry.title, entry.unique_id, True)
    # entry.async_on_unload(coordinator.async_start())

    # if not await coordinator.async_wait_ready():
    #     raise ConfigEntryNotReady(f"{address} is not advertising state")

    # entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


asyncio.run(main())
