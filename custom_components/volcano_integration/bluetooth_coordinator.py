"""Bluetooth Coordinator for the Volcano Integration.

- References to 'fan' changed to 'pump'
- Adds a write_gatt_char for setting heater temperature (UUID=10110003-...).
- Still uses older 'await is_connected()' and 'await get_services()' with FutureWarnings.
"""

import asyncio
import logging
import time

from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"

# GATT Characteristic UUIDs
UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"       # Current Temperature
UUID_PUMP_NOTIFICATIONS = "1010000c-5354-4f52-5a26-4249434b454c"  # Pump notifications (was fan)
UUID_PUMP_ON  = "10110013-5354-4f52-5a26-4249434b454c"
UUID_PUMP_OFF = "10110014-5354-4f52-5a26-4249434b454c"
UUID_HEAT_ON  = "1011000f-5354-4f52-5a26-4249434b454c"
UUID_HEAT_OFF = "10110010-5354-4f52-5a26-4249434b454c"

# **NEW**: Heater setpoint write UUID
UUID_HEATER_SETPOINT = "10110003-5354-4f52-5a26-4249434b454c"

# Timings
RECONNECT_INTERVAL = 3
POLL_INTERVAL = 0.5
RSSI_INTERVAL = 60.0

# Pump patterns (was fan) for the 2 bytes: (heat_byte, pump_byte)
VALID_PATTERNS = {
    (0x23, 0x00): ("ON", "OFF"),
    (0x00, 0x00): ("OFF", "OFF"),
    (0x00, 0x30): ("OFF", "ON"),
    (0x23, 0x30): ("ON", "ON"),
}


class VolcanoBTManager:
    """
    Background loop that:
     - Polls temperature every 0.5s
     - Subscribes to pump notifications
     - Reads RSSI every 60s (if supported)
     - Exposes write_gatt_command() for Pump/Heat On/Off
     - **New**: set_heater_temperature() to write a setpoint (range 40–230).
    """

    def __init__(self):
        self._hass = None
        self._client = None
        self._connected = False

        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None  # was fan_state
        self.rssi = None

        self.bt_status = "DISCONNECTED"

        self._task = None
        self._stop_event = asyncio.Event()
        self._sensors = []

        self._last_rssi_time = 0.0

    def register_sensor(self, sensor_entity):
        if sensor_entity not in self._sensors:
            self._sensors.append(sensor_entity)

    def unregister_sensor(self, sensor_entity):
        if sensor_entity in self._sensors:
            self._sensors.remove(sensor_entity)

    def start(self, hass):
        _LOGGER.debug("VolcanoBTManager.start() -> creating background task.")
        self._hass = hass
        self._stop_event.clear()
        self._task = hass.loop.create_task(self._run())

    def stop(self):
        _LOGGER.debug("VolcanoBTManager.stop() -> stopping background task.")
        if self._task and not self._task.done():
            self._stop_event.set()

    async def _run(self):
        _LOGGER.debug("Entering VolcanoBTManager._run() loop.")
        while not self._stop_event.is_set():
            if not self._connected:
                await self._connect()

            if self._connected:
                # Poll temperature
                await self._read_temperature()

                # Periodically read RSSI
                now = time.time()
                if (now - self._last_rssi_time) >= RSSI_INTERVAL:
                    await self._read_rssi()
                    self._last_rssi_time = now

            await asyncio.sleep(POLL_INTERVAL)

        _LOGGER.debug("Exiting VolcanoBTManager._run() loop -> disconnecting.")
        await self._disconnect()

    async def _connect(self):
        """Attempt to connect to the BLE device (await is_connected() approach)."""
        try:
            _LOGGER.info("Connecting to Bluetooth device %s...", BT_DEVICE_ADDRESS)
            self.bt_status = "CONNECTING"

            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()
            await self._client.get_services()  # triggers FutureWarning, but helps on HA OS

            self._connected = await self._client.is_connected()  # triggers FutureWarning

            if self._connected:
                _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                self.bt_status = "CONNECTED"
                await self._subscribe_pump_notifications()
            else:
                _LOGGER.warning(
                    "Connection to %s unsuccessful. Retrying in %s sec...",
                    BT_DEVICE_ADDRESS, RECONNECT_INTERVAL
                )
                self.bt_status = "DISCONNECTED"
                await asyncio.sleep(RECONNECT_INTERVAL)

        except BleakError as e:
            err_str = f"ERROR: {e}"
            _LOGGER.error(
                "Bluetooth connect error: %s -> Retrying in %s sec...",
                err_str, RECONNECT_INTERVAL
            )
            self.bt_status = err_str
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _subscribe_pump_notifications(self):
        """Subscribe to the pump notifications (2-byte pattern)."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to pump notifications: not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            _LOGGER.debug("Pump notification raw: %s", data.hex())
            if len(data) >= 2:
                b1, b2 = data[0], data[1]
                if (b1, b2) in VALID_PATTERNS:
                    heat_val, pump_val = VALID_PATTERNS[(b1, b2)]
                    self.heat_state = heat_val
                    self.pump_state = pump_val
                    _LOGGER.debug(
                        "Parsed pump => heat=%s, pump=%s (pattern=(0x%02x, 0x%02x))",
                        heat_val, pump_val, b1, b2
                    )
                else:
                    self.heat_state = "UNKNOWN"
                    self.pump_state = "UNKNOWN"
                    _LOGGER.warning(
                        "Unknown pump pattern (0x%02x, 0x%02x).", b1, b2
                    )
            else:
                self.heat_state = "UNKNOWN"
                self.pump_state = "UNKNOWN"
                _LOGGER.warning("Pump notification too short: %d byte(s).", len(data))

            self._notify_sensors()

        try:
            _LOGGER.info("Subscribing to pump notifications on UUID %s", UUID_PUMP_NOTIFICATIONS)
            await self._client.start_notify(UUID_PUMP_NOTIFICATIONS, notification_handler)
            _LOGGER.debug("Pump subscription active.")
        except BleakError as e:
            err_str = f"ERROR subscribing to pump: {e}"
            _LOGGER.error(err_str)
            self.bt_status = err_str

    async def _read_temperature(self):
        """Read the temperature characteristic every 0.5s."""
        if not self._connected or not self._client:
            _LOGGER.debug("Not connected -> skipping temperature read.")
            return

        try:
            data = await self._client.read_gatt_char(UUID_TEMP)
            _LOGGER.debug("Read temperature raw bytes: %s", data.hex())

            if len(data) < 2:
                _LOGGER.warning("Temperature data too short: %d bytes", len(data))
                self.current_temperature = None
            else:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
                _LOGGER.debug(
                    "Parsed temperature = %.1f °C (raw=%d)",
                    self.current_temperature, raw_16
                )

            self._notify_sensors()

        except BleakError as e:
            _LOGGER.error("Error reading temperature: %s -> disconnect & retry...", e)
            self.bt_status = f"ERROR: {e}"
            await self._disconnect()

    async def _read_rssi(self):
        """Read the RSSI (dBm) every 60s, if supported by the backend."""
        if not self._connected or not self._client:
            _LOGGER.debug("Not connected -> skipping RSSI read.")
            return

        try:
            rssi_val = await self._client.get_rssi()
        except (AttributeError, NotImplementedError) as e_attr:
            _LOGGER.debug("get_rssi() not implemented: %s", e_attr)
            rssi_val = None
        except BleakError as e:
            _LOGGER.error("BleakError while reading RSSI: %s", e)
            rssi_val = None

        if rssi_val is not None:
            _LOGGER.debug("Read RSSI = %s dBm", rssi_val)
            self.rssi = rssi_val
        else:
            self.rssi = None
            _LOGGER.debug("RSSI not supported or returned None.")

        self._notify_sensors()

    def _notify_sensors(self):
        for sensor_entity in self._sensors:
            sensor_entity.schedule_update_ha_state(True)

    async def _disconnect(self):
        if self._client:
            _LOGGER.debug("Disconnecting from device %s.", BT_DEVICE_ADDRESS)
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)

        self._client = None
        self._connected = False
        self.bt_status = "DISCONNECTED"
        _LOGGER.info("Disconnected from device %s.", BT_DEVICE_ADDRESS)

    # -------------------------------------------------------------------------
    # Write GATT Command: Pump/Heat ON/OFF
    # -------------------------------------------------------------------------
    async def write_gatt_command(self, write_uuid: str):
        """Write an empty payload to turn Pump/Heat ON/OFF."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot write to %s - not connected.", write_uuid)
            return

        try:
            _LOGGER.debug("Writing GATT char %s -> empty payload", write_uuid)
            await self._client.write_gatt_char(write_uuid, b"")
            _LOGGER.info("Successfully wrote to %s", write_uuid)
        except BleakError as e:
            _LOGGER.error("Error writing to %s: %s", write_uuid, e)
            self.bt_status = f"ERROR: {e}"
            self._notify_sensors()

    # -------------------------------------------------------------------------
    # **NEW**: Set Heater Temperature (40–230)
    # -------------------------------------------------------------------------
    async def set_heater_temperature(self, temp_c: float):
        """
        Write the temperature setpoint to the heater's GATT characteristic (UUID_HEATER_SETPOINT).
        We'll assume it's a 16-bit int in tenths of a degree, like the other code.

        E.g., 40.0 -> b"\x90\x00"  (i.e. 400 in 16-bit little-endian)
              230.0 -> b"\x06\x09" (2300 in decimal)
        """
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set heater temperature - not connected.")
            return

        # Clamp the input 40.0–230.0
        safe_temp = max(40.0, min(temp_c, 230.0))
        setpoint_int = int(safe_temp * 10)  # store as tenths
        setpoint_bytes = setpoint_int.to_bytes(2, byteorder="little", signed=False)

        _LOGGER.debug(
            "Writing heater temperature=%.1f °C -> raw=%s (hex=%s)",
            safe_temp, setpoint_bytes, setpoint_bytes.hex()
        )

        try:
            await self._client.write_gatt_char(UUID_HEATER_SETPOINT, setpoint_bytes)
            _LOGGER.info(
                "Heater setpoint updated to %.1f °C (raw %s) at UUID %s",
                safe_temp, setpoint_bytes.hex(), UUID_HEATER_SETPOINT
            )
        except BleakError as e:
            _LOGGER.error("Error writing heater temp: %s", e)
            self.bt_status = f"ERROR: {e}"
            self._notify_sensors()

    # -------------------------------------------------------------------------
    # Connect/Disconnect button methods
    # -------------------------------------------------------------------------
    async def async_user_connect(self):
        """User pressed 'Connect' button."""
        _LOGGER.debug("User pressed Connect button -> re-connecting BLE.")
        self.stop()
        if self._task and not self._task.done():
            _LOGGER.debug("Waiting for old task to finish before reconnect.")
            await self._task

        self._stop_event.clear()
        self._task = self._hass.loop.create_task(self._run())

    async def async_user_disconnect(self):
        """User pressed 'Disconnect' button."""
        _LOGGER.debug("User pressed Disconnect button -> stopping BLE.")
        self.stop()
        if self._task and not self._task.done():
            _LOGGER.debug("Waiting for old task to exit.")
            await self._task

        await self._disconnect()
        self.bt_status = "DISCONNECTED"
        _LOGGER.debug("Set bt_status to DISCONNECTED after user request.")
        self._notify_sensors()
