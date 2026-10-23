"""Driver for the Turing Smart Screen 3.5" (revision A, serial "USB35INCHIPSV2").

Protocol based on the open source project turing-smart-screen-python (mathoudebine).
"""
import time

import numpy as np
from PIL import Image

NATIVE_W, NATIVE_H = 320, 480

ORIENTATIONS = {"portrait": 0, "portrait_flipped": 1, "landscape": 2, "landscape_flipped": 3}


class Cmd:
    RESET = 101
    CLEAR = 102
    SCREEN_OFF = 108
    SCREEN_ON = 109
    SET_BRIGHTNESS = 110
    SET_ORIENTATION = 121
    DISPLAY_BITMAP = 197


def size_for(orientation):
    if orientation.startswith("portrait"):
        return NATIVE_W, NATIVE_H
    return NATIVE_H, NATIVE_W


# other smart screens that use a different protocol (not supported yet): how to recognize them
OTHER_SCREENS = (
    (lambda p: p.serial_number == "2017-2-25", '3.5" revision B (XuanFang)'),
    (lambda p: (p.vid, p.pid) in ((0x1D6B, 0x0121), (0x1D6B, 0x0106)), 'Turing 2.1" / 5" / 8.8" (revision C)'),
    (lambda p: (p.vid, p.pid) == (0x454D, 0x4E41), "Kipye (revision D)"),
)


def other_screen(port):
    """Name of a known but unsupported screen model, or None."""
    return next((name for match, name in OTHER_SCREENS if match(port)), None)


def is_turing(port):
    if other_screen(port):
        return False
    return port.serial_number == "USB35INCHIPSV2" or (port.vid, port.pid) == (0x1A86, 0x5722)


def unsupported_found():
    """Names of connected screens that Tela! cannot drive (for a clear message instead of "not found")."""
    try:
        from serial.tools.list_ports import comports
        return sorted({n for n in (other_screen(p) for p in comports()) if n})
    except Exception:  # noqa: BLE001
        return []


def find_port():
    from serial.tools.list_ports import comports
    ports = list(comports())
    for p in ports:
        if p.serial_number == "USB35INCHIPSV2":
            return p.device
    for p in ports:
        if is_turing(p):
            return p.device
    return None


def list_ports():
    """[(device, description)] for the port picker."""
    try:
        from serial.tools.list_ports import comports
        out = []
        for p in sorted(comports(), key=lambda p: p.device):
            desc = 'Turing Smart Screen 3.5"' if is_turing(p) else (p.description or "")
            out.append((p.device, desc[:60]))
        return out
    except Exception:  # noqa: BLE001
        return []


def to_rgb565(img):
    a = np.asarray(img.convert("RGB"), dtype=np.uint16)
    r = (a[..., 0] >> 3) << 11
    g = (a[..., 1] >> 2) << 5
    b = a[..., 2] >> 3
    return (r | g | b).astype("<u2").tobytes()


class TuringScreen:
    def __init__(self, port="auto", orientation="landscape", brightness=40):
        if orientation not in ORIENTATIONS:
            raise ValueError(f"invalid orientation: {orientation} (use {', '.join(ORIENTATIONS)})")
        self.port = port
        self.orientation = orientation
        self.brightness = brightness
        self.width, self.height = size_for(orientation)
        self.ser = None
        self.port_in_use = None
        self.bytes_sent = 0

    def _open(self):
        import serial
        port = self.port
        if port in (None, "", "auto"):
            port = find_port()
            if not port:
                other = unsupported_found()
                if other:
                    raise RuntimeError("unsupported screen: " + ", ".join(other))
                raise RuntimeError("screen not found")
        self.ser = serial.Serial(port, 115200, timeout=1, write_timeout=10, rtscts=True)
        self.port_in_use = port

    def connect(self, reset=True):
        self._open()
        if reset:
            # reset, wait for the screen to reboot and reopen (the COM port may change)
            self._cmd(Cmd.RESET)
            self.close()
            time.sleep(5)
            for _ in range(10):
                try:
                    self._open()
                    break
                except Exception:  # noqa: BLE001
                    time.sleep(1)
            else:
                self._open()
        self._cmd(Cmd.SCREEN_ON)
        self.set_brightness(self.brightness)
        self.set_orientation(self.orientation)

    def _cmd(self, cmd, x=0, y=0, ex=0, ey=0):
        buf = bytearray(6)
        buf[0] = (x >> 2) & 0xFF
        buf[1] = (((x & 3) << 6) + (y >> 4)) & 0xFF
        buf[2] = (((y & 15) << 4) + (ex >> 6)) & 0xFF
        buf[3] = (((ex & 63) << 2) + (ey >> 8)) & 0xFF
        buf[4] = ey & 0xFF
        buf[5] = cmd
        self.ser.write(bytes(buf))

    def set_brightness(self, pct):
        pct = max(0, min(100, int(pct)))
        self.brightness = pct
        if self.ser is not None:
            self._cmd(Cmd.SET_BRIGHTNESS, int(255 - pct / 100 * 255))

    def set_orientation(self, orientation):
        self.orientation = orientation
        self.width, self.height = size_for(orientation)
        if self.ser is None:
            return
        w, h = size_for(orientation)
        buf = bytearray(16)
        buf[5] = Cmd.SET_ORIENTATION
        buf[6] = ORIENTATIONS[orientation] + 100
        buf[7], buf[8] = w >> 8, w & 0xFF
        buf[9], buf[10] = h >> 8, h & 0xFF
        self.ser.write(bytes(buf))

    def turn_off(self):
        """Black screen (brightness 0 + screen off). The reset on the next connect turns it back on."""
        if self.ser is None:
            return
        self._cmd(Cmd.SET_BRIGHTNESS, 255)
        self._cmd(Cmd.SCREEN_OFF)
        try:
            self.ser.flush()
        except Exception:  # noqa: BLE001
            pass

    def turn_on(self):
        if self.ser is None:
            return
        self._cmd(Cmd.SCREEN_ON)
        self.set_brightness(self.brightness)

    def send_image(self, img, x, y):
        w, h = img.size
        self._cmd(Cmd.DISPLAY_BITMAP, x, y, x + w - 1, y + h - 1)
        data = to_rgb565(img)
        step = self.width * 8
        for i in range(0, len(data), step):
            self.ser.write(data[i:i + step])
        self.bytes_sent += len(data)

    def end_frame(self):
        pass

    def close(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:  # noqa: BLE001
                pass
        self.ser = None


class SimulatedScreen:
    """No hardware: builds the frame in memory and saves a PNG on every update."""

    def __init__(self, orientation="landscape", file="preview.png", bytes_per_second=None):
        self.orientation, self.brightness, self.port = orientation, 40, "simulated"
        self.width, self.height = size_for(orientation)
        self.file = str(file) if file else None
        self.buffer = Image.new("RGB", (self.width, self.height))
        self.port_in_use = "simulated"
        self.bytes_sent = 0
        self.bytes_per_second = bytes_per_second   # set to ~128000 to imitate the real screen

    def connect(self, reset=True):
        pass

    def set_brightness(self, pct):
        self.brightness = pct

    def set_orientation(self, orientation):
        self.orientation = orientation
        self.width, self.height = size_for(orientation)
        if self.buffer.size != (self.width, self.height):
            self.buffer = Image.new("RGB", (self.width, self.height))

    def turn_off(self):
        self.buffer.paste((0, 0, 0), (0, 0, self.width, self.height))
        self.end_frame()

    def turn_on(self):
        pass

    def send_image(self, img, x, y):
        self.buffer.paste(img, (x, y))
        n = img.size[0] * img.size[1] * 2
        self.bytes_sent += n
        if self.bytes_per_second:
            time.sleep(n / self.bytes_per_second)

    def end_frame(self):
        if self.file:
            self.buffer.save(self.file)

    def close(self):
        pass
