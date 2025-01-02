"""Bluetooth Coordinator for the Volcano Integration."""

import asyncio
import logging
from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"
RECONNECT_INTERVAL = 3
TEMP_POLL_INTERVAL = 1

VALID_PATTERNS = {
    (0x23, 0x00): ("ON", "OFF"),
    (0x00, 0x00): ("OFF", "OFF"),
    (0x00, 0x30): ("OFF", "ON"),
    (0x23, 0x30): ("ON", "ON"),
    (0x23, 0x06): ("TARGET MET (BURSTING)", "ON"),
    (0x23, 0x26): ("TARGET MET", "ON"),
    (0x23, 0x36): ("OVER TARGET", "ON"),
}


class VolcanoBTManager:
    def __init__(self):
        self._client = None
        self._connected = False

        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None
        self.target_status = None

        self.bt_status = "DISCONNECTED"

        self._run_task = None
        self._temp_poll_task = None
        self._stop_event = asyncio.Event()
        self._sensors = []

        self.UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"
        self.UUID_PUMP_NOTIFICATIONS = "1010000c-5354-4f52-5a26-4249434b454c"
        self.UUID_PUMP_ON = "10110013-5354-4f52-5a26-4249434b454c"
        self.UUID_PUMP_OFF = "10110014-5354-4f52-5a26-4249434b454c"
        self.UUID_HEAT_ON = "1011000f-5354-4f52-5a26-4249434b454c"
        self.UUID_HEAT_OFF = "10110010-5354-4f52-5a26-4249434b454c"
        self.UUID_HEATER_SETPOINT = "10110003-5354-4f52-5a26-4249434b454c"

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
            _LOGGER.info("Connecting to Bluetooth device %s...", BT_DEVICE_ADDRESS)
            self.bt_status = "CONNECTING"
            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()
            self._connected = self._client.is_connected

            if self._connected:
                _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                self.bt_status = "CONNECTED"
                await self._subscribe_pump_notifications()
            else:
                _LOGGER.warning("Connection unsuccessful. Retrying in %s sec...", RECONNECT_INTERVAL)
                self.bt_status = "DISCONNECTED"
                await asyncio.sleep(RECONNECT_INTERVAL)

        except BleakError as e:
            err_str = f"ERROR: {e}"
            _LOGGER.error("Bluetooth connect error: %s -> Retrying in %s sec...", err_str, RECONNECT_INTERVAL)
            self.bt_status = err_str
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _subscribe_pump_notifications(self):
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to pump notifications: not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            _LOGGER.debug("Pump notification raw: %s", data.hex())
            if len(data) >= 2:
                b1, b2 = data[0], data[1]
                _LOGGER.debug("Received bytes: 0x%02x, 0x%02x", b1, b2)

                if (b1, b2) in VALID_PATTERNS:
                    heat_val, pump_val = VALID_PATTERNS[(b1, b2)]
                    self.heat_state = "ON" if "ON" in heat_val else "OFF"
                    self.target_status = heat_val
                else:
                    self.target_status = f"RAW: {b1:02x}{b2:02x}"
                    self.heat_state = "UNKNOWN"

                self.pump_state = pump_val
            else:
                self.heat_state = "UNKNOWN"
                self.pump_state = "UNKNOWN"
                self.target_status = "UNKNOWN"
            self._notify_sensors()

        try:
            await self._client.start_notify(self.UUID_PUMP_NOTIFICATIONS, notification_handler)
            _LOGGER.debug("Pump subscription active.")
        except BleakError as e:
            err_str = f"ERROR subscribing to pump: {e}"
            _LOGGER.error(err_str)
            self.bt_status = err_str

    async def _poll_temperature(self):
        while not self._stop_event.is_set():
            if self._connected:
                await self._read_temperature()
            await asyncio.sleep(TEMP_POLL_INTERVAL)

    async def _read_temperature(self):
        if not self._connected or not self._client:
            return
        try:
            data = await self._client.read_gatt_char(self.UUID_TEMP)
            if len(data) < 2:
                self.current_temperature = None
            else:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
            self._notify_sensors()
        except BleakError as e:
            self.bt_status = f"ERROR: {e}"
            await self._disconnect()

    def _notify_sensors(self):
        for sensor_entity in self._sensors:
            sensor_entity.schedule_update_ha_state(True)

    async def _disconnect(self):
        if self._client:
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)
        self._client = None
        self._connected = False
        self.bt_status = "DISCONNECTED"

---

### **Updated `sensor.py`**
```python
class VolcanoTemperatureTargetStatusSensor(VolcanoBaseSensor):
    """Temperature Target Status Sensor."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Temperature Target Status"
        self._attr_unique_id = "volcano_temperature_target_status"
        self._attr_icon = "mdi:target"

    @property
    def native_value(self):
        return self._manager.target_status

    @property
    def available(self):
        return self._manager.bt_status == "CONNECTED"
