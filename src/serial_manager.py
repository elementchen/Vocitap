import asyncio
import json
import logging
import threading
import serial
import serial.tools.list_ports

log = logging.getLogger(__name__)

class SppClient:
    """Connects to ESP32 SPP server / USB Serial via virtual COM port."""

    def __init__(self):
        self._ser = None
        self._port = None
        self._connected = False
        self._read_thread = None
        self._loop = None
        
        # Callbacks registered by the SerialManager
        self.on_button_event = None   # callback(button_id: int, state: int)
        self.on_status = None         # callback(hfp: int, audio: int)
        self.on_disconnect = None     # callback()

        # Future used to wait for responses of commands
        self._response_future = None
        
        # Local configuration cache populated on connection
        self._config_cache = {}
        
        # OTA mode flag and queue for flow control
        self._ota_mode = False
        self._ota_queue = asyncio.Queue()

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def address(self) -> str | None:
        """Expose the current COM port name to mimic the original BLE address API."""
        return self._port

    @staticmethod
    def list_ports() -> list[dict]:
        """List all COM ports, sorting likely Bluetooth ports to the top."""
        ports = serial.tools.list_ports.comports()
        result = []
        for p in ports:
            name = p.device
            desc = p.description or ""
            hwid = p.hwid or ""
            
            # Identify potential bluetooth virtual serial ports
            is_bt = False
            bt_keywords = ["bluetooth", "btport", "bthenum", "蓝牙", "标准串行"]
            if any(kw in desc.lower() or kw in hwid.lower() for kw in bt_keywords):
                is_bt = True
                
            result.append({
                "port": name,
                "desc": f"{name} ({desc})",
                "is_bt": is_bt
            })
            
        # Sort so that Bluetooth ports appear first (if any)
        result.sort(key=lambda x: x["is_bt"], reverse=True)
        return result

    async def connect(self, port: str) -> bool:
        """Open the serial port, start the read thread, and fetch configuration."""
        try:
            log.info(f"Connecting to serial port {port}...")
            # Configure PySerial without triggering auto-reset flags where supported
            self._ser = serial.Serial()
            self._ser.port = port
            self._ser.baudrate = 115200
            self._ser.timeout = 1.0
            self._ser.rtscts = False
            self._ser.dsrdtr = False
            self._ser.open()
            
            # Explicitly clear DTR and RTS pin levels to try avoiding ESP32 reset
            try:
                self._ser.dtr = False
                self._ser.rts = False
            except Exception:
                pass
                
            self._port = port
            self._connected = True
            
            # Capture the current asyncio event loop to dispatch events safely
            self._loop = asyncio.get_running_loop()
            
            # Start background reading thread
            self._read_thread = threading.Thread(target=self._run_read_loop, daemon=True)
            self._read_thread.start()
            
            # Delay to wait for ESP32 boot sequence to finish if reset was triggered
            log.info("Waiting 2.5 seconds for device boot stabilization...")
            await asyncio.sleep(2.5)
            
            # Fetch device configuration to populate cache
            ok = await self._fetch_config()
            if not ok:
                log.warning("Failed to fetch initial configuration from device.")
                
            log.info(f"SPP Client successfully connected to {port}")
            return True
        except Exception as e:
            log.error(f"Failed to connect to {port}: {e}")
            self.disconnect_sync()
            return False

    async def disconnect(self):
        """Asynchronous disconnect wrapper."""
        self.disconnect_sync()

    def disconnect_sync(self):
        """Synchronously close the port and join reader thread."""
        was_connected = self._connected
        self._connected = False
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        self._port = None
        self._config_cache.clear()
        log.info("SPP Client disconnected")
        if was_connected and self.on_disconnect:
            # Avoid direct callback execution inside potentially closed thread contexts
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self.on_disconnect)
            else:
                self.on_disconnect()

    def _run_read_loop(self):
        """Thread worker to continuously read from the serial port line by line."""
        while self._connected and self._ser:
            try:
                line_bytes = self._ser.readline()
                if not line_bytes:
                    continue
                    
                line = line_bytes.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                    
                log.debug(f"Serial RX: {line}")
                if not line.startswith("{"):
                    log.warning(f"[ESP32 LOG] {line}")
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    log.warning(f"[ESP32 LOG (JSON Parse Fail)] {line}")
                    continue
                
                # Check if it's an unsolicited event from ESP32
                if "event" in data:
                    evt = data["event"]
                    if evt == "btn" and self.on_button_event:
                        btn_id = data.get("id", 0)
                        state = data.get("state", 0)
                        self._loop.call_soon_threadsafe(self.on_button_event, btn_id, state)
                    elif evt == "status" and self.on_status:
                        hfp = data.get("hfp", 0)
                        audio = data.get("audio", 0)
                        self._loop.call_soon_threadsafe(self.on_status, hfp, audio)
                        
                # Check if it's a command response
                elif "status" in data:
                    if self._ota_mode:
                        self._loop.call_soon_threadsafe(self._ota_queue.put_nowait, data)
                    else:
                        # Dispatch to the waiting future with race condition protection
                        fut = self._response_future
                        if fut and not fut.done():
                            self._response_future = None  # Block subsequent arrivals from touching this future
                            self._loop.call_soon_threadsafe(fut.set_result, data)
                        
            except Exception as e:
                log.error(f"Error in read loop: {e}")
                if self._connected:
                    # Trigger disconnect in case of hardware error
                    self._loop.call_soon_threadsafe(self.disconnect_sync)
                break

    async def _send_cmd(self, cmd_dict: dict, timeout: float = 2.0) -> dict | None:
        """Send a JSON command and wait asynchronously for its response."""
        if not self._connected or not self._ser:
            return None
            
        # Create a new future for this command
        self._response_future = self._loop.create_future()
        
        try:
            cmd_str = json.dumps(cmd_dict) + "\n"
            self._ser.write(cmd_str.encode("utf-8"))
            
            # Wait for response future to resolve
            resp = await asyncio.wait_for(self._response_future, timeout=timeout)
            return resp
        except Exception as e:
            log.error(f"Command {cmd_dict.get('cmd')} failed: {e}")
            return None
        finally:
            self._response_future = None

    async def _fetch_config(self) -> bool:
        """Fetch the full configuration from ESP32 and save in cache."""
        for attempt in range(3):
            log.info(f"Fetching configuration from device (attempt {attempt + 1}/3)...")
            resp = await self._send_cmd({"cmd": "get_config"}, timeout=1.5)
            if resp and resp.get("status") == "ok":
                self._config_cache = resp
                return True
            await asyncio.sleep(1.0)
        return False

    async def read_button_mapping(self, idx: int) -> tuple[int, int] | None:
        """Return the (vk_code, modifier) for button index from cache."""
        # Use cached values. If not cached, attempt a fetch
        if not self._config_cache:
            await self._fetch_config()
            
        vk_key = f"btn{idx+1}_vk"
        mod_key = f"btn{idx+1}_mod"
        
        if vk_key in self._config_cache and mod_key in self._config_cache:
            return self._config_cache[vk_key], self._config_cache[mod_key]
        return None

    async def write_button_mapping(self, idx: int, vk: int, mod: int) -> bool:
        """Send command to save button mapping on the ESP32."""
        resp = await self._send_cmd({
            "cmd": "set_btn",
            "idx": idx,
            "vk": vk,
            "mod": mod
        })
        if resp and resp.get("status") == "ok":
            # Update local cache
            self._config_cache[f"btn{idx+1}_vk"] = vk
            self._config_cache[f"btn{idx+1}_mod"] = mod
            return True
        return False

    async def read_tx_power(self) -> int | None:
        """Get the Classic BT / BLE TX power level from cache."""
        if not self._config_cache:
            await self._fetch_config()
        return self._config_cache.get("tx_power")

    async def write_tx_power(self, level: int) -> bool:
        """Save TX power level to the ESP32."""
        resp = await self._send_cmd({
            "cmd": "set_tx_power",
            "level": level
        })
        if resp and resp.get("status") == "ok":
            self._config_cache["tx_power"] = level
            return True
        return False

    async def read_mic_enabled(self) -> int | None:
        """Get the mic enabled flag from cache."""
        if not self._config_cache:
            await self._fetch_config()
        return self._config_cache.get("mic_enabled")

    async def write_mic_enabled(self, enabled: int) -> bool:
        """Save mic enabled configuration to the ESP32."""
        resp = await self._send_cmd({
            "cmd": "set_mic_enabled",
            "enabled": enabled
        })
        if resp and resp.get("status") == "ok":
            self._config_cache["mic_enabled"] = enabled
            return True
        return False

    async def read_firmware_version(self) -> str:
        """Get the current firmware version from cache."""
        if not self._config_cache:
            await self._fetch_config()
        return self._config_cache.get("version", "Unknown")

    async def upload_firmware(self, bin_path: str, progress_callback=None, mode="classic") -> bool:
        """Upload firmware .bin file to ESP32 via chunked VFS serial OTA protocol."""
        if not self._connected or not self._ser:
            log.error("OTA failed: Serial client is not connected.")
            return False
            
        try:
            with open(bin_path, "rb") as f:
                bin_data = f.read()
        except Exception as e:
            log.error(f"Failed to read firmware binary file: {e}")
            return False
            
        total_size = len(bin_data)
        log.info(f"Starting OTA update. Firmware size: {total_size} bytes (Mode: {mode})...")
        
        # Clear any stale data in ota_queue
        while not self._ota_queue.empty():
            self._ota_queue.get_nowait()
            
        # 1. Send ota_start command (using 10.0s timeout to allow partition flash erasing)
        resp = await self._send_cmd({"cmd": "ota_start", "size": total_size}, timeout=10.0)
        if not resp:
            log.error("OTA start failed: No response from device.")
            return False
            
        if resp.get("status") == "ok" and resp.get("reboot") == 1:
            # Device needs reboot into clean OTA mode
            log.info("Device is rebooting into clean OTA mode to ensure zero-interference flash erase...")
            
            # Remember current port to reconnect
            port = self._ser.port
            await self.disconnect()
            
            # Wait 3.0s for device to reboot and initialize serial console
            await asyncio.sleep(3.0)
            
            log.info(f"Reconnecting to {port} in clean OTA mode...")
            if not await self.connect(port):
                log.error("Failed to reconnect in clean OTA mode.")
                return False
                
            # Resend ota_start under clean mode
            log.info("Re-sending OTA start handshake in clean mode...")
            resp = await self._send_cmd({"cmd": "ota_start", "size": total_size}, timeout=10.0)
            if not resp or resp.get("status") != "ok":
                log.error(f"Clean OTA start failed: {resp.get('reason') if resp else 'No response'}")
                return False
        elif resp.get("status") != "ok":
            log.error(f"OTA start failed: {resp.get('reason')}")
            return False
            
        log.info("OTA handshake success. Transferring binary payload in chunks...")
        
        # Enable OTA mode to route responses into ota_queue
        self._ota_mode = True
        
        try:
            # 2. Loop to write binary chunks with strict flow control (Classic Sync Mode)
            # Optimized to synchronize every 16KB to prevent full-duplex driver lockups,
            # while strictly validating progress to prevent false success.
            # Using 256 bytes chunks to drastically shorten single packet physical transmission time (22ms at 115200).
            # This eliminates the risk of UART FIFO overrun during concurrent Flash Block Erase cycles,
            # as no data flows on the wire while the ESP32 is busy performing internal flash writes.
            chunk_size = 256
            current_total = 0
            for i in range(0, total_size, chunk_size):
                chunk = bin_data[i:i+chunk_size]
                expected_total = i + len(chunk)
                
                # 1. Pre-emit sync for trailing tail chunk to prevent final block overflow
                # Since the ESP32 firmware emits progress packets strictly at 1KB boundaries,
                # we synchronize up to the nearest 1KB multiple to prevent handshake deadlocks on fractional blocks.
                is_last_chunk = (i + chunk_size >= total_size)
                if is_last_chunk and i > 0:
                    target_sync = (i // 1024) * 1024
                    log.info(f"Syncing prior blocks with board before sending tail chunk (confirmed: {current_total}/{target_sync})...")
                    try:
                        while current_total < target_sync:
                            chunk_resp = await asyncio.wait_for(self._ota_queue.get(), timeout=8.0)
                            if chunk_resp:
                                if chunk_resp.get("status") == "error":
                                    log.error(f"OTA tail-sync failed: {chunk_resp.get('reason')}")
                                    return False
                                if chunk_resp.get("status") == "done":
                                    log.info("OTA upgrade completed successfully! The device is now rebooting.")
                                    return True
                                current_total = max(current_total, chunk_resp.get("total_written", 0))
                    except asyncio.TimeoutError:
                        log.error(f"Timeout waiting for sync before tail chunk. Confirmed: {current_total}/{target_sync}")
                        return False
                    log.info("Sync complete. Emitting trailing fractional chunk...")
                    
                self._ser.write(chunk)
                self._ser.flush()  # Force OS port to instantly emit binary buffer
                
                # 2. Non-blocking update of progress queue
                while not self._ota_queue.empty():
                    try:
                        chunk_resp = self._ota_queue.get_nowait()
                        if chunk_resp:
                            if chunk_resp.get("status") == "error":
                                log.error(f"OTA chunk write failed: {chunk_resp.get('reason')}")
                                return False
                            if chunk_resp.get("status") == "done":
                                log.info("OTA upgrade completed successfully! The device is now rebooting.")
                                return True
                            current_total = max(current_total, chunk_resp.get("total_written", 0))
                    except asyncio.QueueEmpty:
                        break
                        
                # 3. Synchronize strictly every 16KB to prevent Windows serial driver lockup
                # while ensuring absolute safety against buffer overrun.
                # We synchronize up to the nearest 1KB multiple to match ESP32's 1KB ACK boundaries.
                if i > 0 and i % (1024 * 16) == 0:
                    target_sync = (i // 1024) * 1024
                    try:
                        while current_total < target_sync:
                            chunk_resp = await asyncio.wait_for(self._ota_queue.get(), timeout=10.0)
                            if chunk_resp:
                                if chunk_resp.get("status") == "error":
                                    log.error(f"OTA sync failed: {chunk_resp.get('reason')}")
                                    return False
                                if chunk_resp.get("status") == "done":
                                    log.info("OTA upgrade completed successfully! The device is now rebooting.")
                                    return True
                                current_total = max(current_total, chunk_resp.get("total_written", 0))
                    except asyncio.TimeoutError:
                        log.error(f"OTA handshake timeout waiting for {target_sync} bytes. Current confirmed: {current_total}")
                        return False
                    
                if progress_callback:
                    progress_callback(max(current_total, expected_total), total_size)
                    
                # Yield control for 5ms to allow host UART driver and power ripple stabilization.
                # Since chunk_size is 256 bytes, 5ms is extremely safe and boosts speed significantly.
                await asyncio.sleep(0.005)
            
            # 3. Wait for final OTA done & partition boot set response (Classic Mode)
            log.info("All firmware chunks sent. Waiting for final verification on device...")
            try:
                while True:
                    final_resp = await asyncio.wait_for(self._ota_queue.get(), timeout=8.0)
                    if not final_resp:
                        log.error("Invalid empty response from device.")
                        return False
                    
                    status = final_resp.get("status")
                    if status == "done":
                        log.info("OTA upgrade completed successfully! The device is now rebooting.")
                        return True
                    elif status == "error":
                        log.error(f"OTA verification failed: {final_resp.get('reason')}")
                        return False
                    elif status in ("progress", "next"):
                        # This is just a trailing chunk progress confirmation, keep waiting for the final validation done signal!
                        log.info(f"Received confirmation progress: {final_resp.get('total_written')}/{total_size}")
                        continue
                    else:
                        log.error(f"Unknown status received: {status}")
                        return False
            except asyncio.TimeoutError:
                log.error("OTA final verification timed out waiting for success confirmation.")
                return False
        finally:
            # Always ensure OTA mode is turned off on exit
            self._ota_mode = False


class SerialManager:
    """Manages physical USB Serial connection to Vocitap hardware, matching BleManager API."""

    def __init__(self):
        self._loop = None
        self._thread = None
        
        self.spp = SppClient()
        self.spp.on_button_event = self._internal_button_handler
        self.spp.on_status = self._internal_status_handler
        self.spp.on_disconnect = self._internal_disconnect_handler

        # Callbacks
        self.on_button_event = None
        self.on_status_change = None
        self.on_device_status = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_coro(self, coro):
        if not self._loop:
            return None
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    @property
    def is_connected(self):
        return self.spp.is_connected

    @property
    def _address(self):
        """Expose current connected port as address to avoid major API refactoring in main.py."""
        return self.spp.address

    def list_ports(self) -> list[dict]:
        """Expose list of system serial ports."""
        return SppClient.list_ports()

    async def _connect_async(self, port):
        ok = await self.spp.connect(port)
        if self.on_status_change:
            self.on_status_change(ok, port if ok else None)
        return ok

    def connect(self, port):
        self._run_coro(self._connect_async(port))

    async def _disconnect_async(self):
        await self.spp.disconnect()
        if self.on_status_change:
            self.on_status_change(False, None)

    def disconnect(self):
        self._run_coro(self._disconnect_async())

    def _internal_button_handler(self, btn_id, state):
        if self.on_button_event:
            self.on_button_event(btn_id, state)

    def _internal_status_handler(self, hfp, audio):
        if self.on_device_status:
            self.on_device_status(hfp, audio)

    def _internal_disconnect_handler(self):
        if self.on_status_change:
            self.on_status_change(False, None)

    async def _read_mapping_async(self, idx, callback):
        res = await self.spp.read_button_mapping(idx)
        if callback:
            callback(res)

    def read_mapping(self, idx, callback):
        self._run_coro(self._read_mapping_async(idx, callback))

    async def _write_mapping_async(self, idx, vk, mod):
        return await self.spp.write_button_mapping(idx, vk, mod)

    def write_mapping(self, idx, vk, mod):
        self._run_coro(self._write_mapping_async(idx, vk, mod))

    async def _read_tx_power_async(self, callback):
        res = await self.spp.read_tx_power()
        if callback:
            callback(res)

    def read_tx_power(self, callback):
        self._run_coro(self._read_tx_power_async(callback))

    async def _write_tx_power_async(self, level):
        return await self.spp.write_tx_power(level)

    def write_tx_power(self, level):
        self._run_coro(self._write_tx_power_async(level))

    async def _read_mic_enabled_async(self, callback):
        res = await self.spp.read_mic_enabled()
        if callback:
            callback(res)

    def read_mic_enabled(self, callback):
        self._run_coro(self._read_mic_enabled_async(callback))

    async def _write_mic_enabled_async(self, enabled):
        return await self.spp.write_mic_enabled(enabled)

    def write_mic_enabled(self, enabled):
        self._run_coro(self._write_mic_enabled_async(enabled))

    async def _read_fw_ver_async(self, callback):
        res = await self.spp.read_firmware_version()
        if callback:
            callback(res)

    def read_fw_version(self, callback):
        self._run_coro(self._read_fw_ver_async(callback))

    async def _upload_firmware_async(self, bin_path, progress_callback):
        return await self.spp.upload_firmware(bin_path, progress_callback)

    def upload_firmware(self, bin_path, progress_callback):
        """Submit OTA firmware upload task to background event loop."""
        return self._run_coro(self._upload_firmware_async(bin_path, progress_callback))
