"""Bluetooth Coordinator for the Volcano Integration."""
import asyncio
import logging
from bleak import BleakClient, BleakError
from .const import (
    UUID_TEMP,
    UUID_PUMP_NOTIFICATIONS,
    UUID_PUMP_ON,
    UUID_PUMP_OFF,
    UUID_HEAT_ON,
    UUID_HEAT_OFF,
    UUID_HEATER_SETPOINT,
    UUID_BLE_FIRMWARE_VERSION,
    UUID_SERIAL_NUMBER,
    UUID_FIRMWARE_VERSION,
    UUID_AUTO_SHUT_OFF,
    UUID_AUTO_SHUT_OFF_SETTING,
    UUID_LED_BRIGHTNESS,
    UUID_HOURS_OF_OPERATION,
    UUID_MINUTES_OF_OPERATION,
    BT_STATUS_DISCONNECTED,
    BT_STATUS_CONNECTING,
    BT_STATUS_CONNECTED,
    BT_STATUS_ERROR,
)

_LOGGER = logging.getLogger(__name__)

BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"
RECONNECT_INTERVAL = 3
TEMP_POLL_INTERVAL = 1

VALID_PATTERNS = {
    (0x23, 0x00): ("ON", "OFF"),
    (0x00, 0x00): ("OFF", "OFF"),
    (0x00, 0x30): ("OFF", "ON"),
    (0x23, 0x30): ("ON", "ON"),
    (0x23, 0x06): ("BURST_STARTED", "ON"),
    (0x23, 0x26): ("BURST_ENDED", "ON"),
}


class VolcanoBTManager:
    def __init__(self):
        self._client = None
        self._connected = False
        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None
        self._bt_status = BT_STATUS_DISCONNECTED
        self._run_task = None
        self._temp_poll_task = None
        self._stop_event = asyncio.Event()
        self._sensors = []
        self.slot_bluetooth_error = False

        # Add attributes for GATT characteristics
        self.ble_firmware_version = None
        self.serial_number = None
        self.firmware_version = None
        self.auto_shut_off = None
        self.auto_shut_off_setting = None
        self.led_brightness = None
        self.hours_of_operation = 0  # Initialize to 0 or None
        self.minutes_of_operation = 0  # Initialize to 0 or None

    @property
    def bt_status(self):
        return self._bt_status

    @bt_status.setter
    def bt_status(self, value):
        if self._bt_status != value:
            _LOGGER.debug("BT status changed from %s to %s", self._bt_status, value)
            self._bt_status = value
            self._notify_sensors()

    def register_sensor(self, sensor_entity):
        if sensor_entity not in self._sensors:
            self._sensors.append(sensor_entity)

    def unregister_sensor(self, sensor_entity):
        if sensor_entity in self._sensors:
            self._sensors.remove(sensor_entity)

    async def start(self):
        if not self._run_task or self._run_task.done():
            self._stop_event.clear()
            self._run_task = asyncio.create_task(self._run())
            self._temp_poll_task = asyncio.create_task(self._poll_temperature())

    async def stop(self):
        if self._run_task and not self._run_task.done():
            self._stop_event.set()
            await self._run_task
        if self._temp_poll_task and not self._temp_poll_task.done():
            self._temp_poll_task.cancel()
            try:
                await self._temp_poll_task
            except asyncio.CancelledError:
                pass
        self.bt_status = BT_STATUS_DISCONNECTED

    async def async_user_connect(self):
        _LOGGER.debug("User requested connection to the Volcano device.")
        if self._connected:
            _LOGGER.info("Already connected to the device.")
            return
        await self.start()

    async def async_user_disconnect(self):
        _LOGGER.debug("User requested disconnection from the Volcano device.")
        if not self._connected:
            _LOGGER.info("Already disconnected from the device.")
            return
        await self.stop()

    async def _run(self):
        _LOGGER.debug("Entering VolcanoBTManager._run() loop.")
        while not self._stop_event.is_set():
            if not self._connected:
                await self._connect()
            await asyncio.sleep(1)
        _LOGGER.debug("Exiting VolcanoBTManager._run() -> disconnecting.")
        await self._disconnect()

    async def _connect(self):
        try:
            _LOGGER.info("Attempting to connect to Bluetooth device %s...", BT_DEVICE_ADDRESS)
            self.bt_status = BT_STATUS_CONNECTING
            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()

            self._connected = self._client.is_connected
            if self._connected:
                _LOGGER.info("Bluetooth successfully connected to %s", BT_DEVICE_ADDRESS)
                self.bt_status = BT_STATUS_CONNECTED

                # Read static attributes once per connection
                await self._read_static_attributes()
                await self._subscribe_pump_notifications()
            else:
                self.bt_status = BT_STATUS_DISCONNECTED
        except BleakError as e:
            _LOGGER.warning("Bluetooth connection warning: %s -> Retrying...", e)
            self.bt_status = BT_STATUS_ERROR
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _read_static_attributes(self):
        """Read static GATT attributes."""
        try:
            self.ble_firmware_version = await self._read_gatt(UUID_BLE_FIRMWARE_VERSION)
            self.serial_number = await self._read_gatt(UUID_SERIAL_NUMBER)
            self.firmware_version = await self._read_gatt(UUID_FIRMWARE_VERSION)
            self.auto_shut_off = await self._read_gatt(UUID_AUTO_SHUT_OFF)
            self.auto_shut_off_setting = await self._read_gatt(UUID_AUTO_SHUT_OFF_SETTING)
            self.led_brightness = await self._read_gatt(UUID_LED_BRIGHTNESS)

            # Read operational times
            self.hours_of_operation = int(await self._read_gatt(UUID_HOURS_OF_OPERATION) or 0)
            self.minutes_of_operation = int(await self._read_gatt(UUID_MINUTES_OF_OPERATION) or 0)

            _LOGGER.debug(
                "Static attributes read: BLE Firmware=%s, Serial=%s, Firmware=%s, Auto Shut Off=%s, "
                "Auto Shut Off Setting=%s, LED Brightness=%s, Hours of Operation=%s, Minutes of Operation=%s",
                self.ble_firmware_version,
                self.serial_number,
                self.firmware_version,
                self.auto_shut_off,
                self.auto_shut_off_setting,
                self.led_brightness,
                self.hours_of_operation,
                self.minutes_of_operation,
            )
        except BleakError as e:
            _LOGGER.warning("Error reading static attributes: %s", e)

    async def _read_gatt(self, uuid):
        """Helper to read GATT characteristic."""
        if not self._connected or not self._client:
            return None
        try:
            data = await self._client.read_gatt_char(uuid)
            return data.decode("utf-8").strip()
        except BleakError as e:
            _LOGGER.warning("Error reading GATT %s: %s", uuid, e)
            return None

    async def _subscribe_pump_notifications(self):
        if not self._connected:
            return

        def notification_handler(sender, data):
            if len(data) >= 2:
                b1, b2 = data[0], data[1]
                if (b1, b2) in VALID_PATTERNS:
                    self.heat_state, self.pump_state = VALID_PATTERNS[(b1, b2)]
                else:
                    self.heat_state = f"0x{b1:02X}"
                    self.pump_state = f"0x{b2:02X}"
            self._notify_sensors()

        try:
            await self._client.start_notify(UUID_PUMP_NOTIFICATIONS, notification_handler)
        except BleakError as e:
            _LOGGER.warning("Error subscribing to notifications: %s", e)

    async def _poll_temperature(self):
        while not self._stop_event.is_set():
            if self._connected:
                await self._read_temperature()
            await asyncio.sleep(TEMP_POLL_INTERVAL)

    async def _read_temperature(self):
        if not self._connected or not self._client:
            return
        try:
            data = await self._client.read_gatt_char(UUID_TEMP)
            if len(data) >= 2:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
            else:
                self.current_temperature = None
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading temperature: %s -> disconnect & retry...", e)
            self.bt_status = BT_STATUS_ERROR
            await self._disconnect()

    def _notify_sensors(self):
        for sensor_entity in self._sensors:
            sensor_entity.schedule_update_ha_state(True)

    async def _disconnect(self):
        if self._client:
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.warning("Bluetooth disconnection warning: %s", e)
        self._client = None
        self._connected = False
        self.bt_status = BT_STATUS_DISCONNECTED

    async def write_gatt_command(self, write_uuid, payload=b""):
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot write to %s - not connected.", write_uuid)
            return
        try:
            await self._client.write_gatt_char(write_uuid, payload)
        except BleakError as e:
            _LOGGER.error("Error writing to %s: %s", write_uuid, e)

    async def set_heater_temperature(self, temp_c):
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set heater temperature - not connected.")
            return
        safe_temp = max(40.0, min(temp_c, 230.0))
        payload = int(safe_temp * 10).to_bytes(2, byteorder="little")
        try:
            await self._client.write_gatt_char(UUID_HEATER_SETPOINT, payload)
        except BleakError as e:
            _LOGGER.error("Error writing heater temperature: %s", e)
