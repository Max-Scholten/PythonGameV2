# python
# file: `controller/joystick.py`
import serial

class ArduinoJoystick:
    """
    Non-blocking Arduino joystick wrapper.
    - Use `poll()` each frame to update `last_data`.
    - `read_input()` returns cached data (never blocks).
    - `get_direction()` returns cardinal direction from cached sample.
    """
    def __init__(self, port, baudrate=9600, deadzone=100):
        # timeout=0 makes reads non-blocking
        self.ser = serial.Serial(port, baudrate, timeout=0)
        self.deadzone = deadzone
        # raw values from Arduino: x,y around 0 (centered by Arduino sketch), a,b are 0/1
        self.last_data = {"x": 0, "y": 0, "a": 0, "b": 0}
        self.updated = False

    def poll(self):
        """Drain available serial input and update last_data (fast, non-blocking)."""
        try:
            # read all available lines
            while self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 4:
                    continue
                try:
                    x, y, a, b = map(int, parts[:4])
                except Exception:
                    continue
                self.last_data = {"x": x, "y": y, "a": a, "b": b}
                self.updated = True
        except Exception:
            # swallow serial errors to avoid stalling the game
            pass

    def read_input(self):
        """Convenience: poll once and return cached data (never blocks)."""
        self.poll()
        return self.last_data

    def get_direction(self):
        """Return cached cardinal direction based on last sampled values."""
        data = self.last_data
        x, y = data.get("x", 0), data.get("y", 0)
        # apply deadzone
        if abs(x) < self.deadzone:
            x = 0
        if abs(y) < self.deadzone:
            y = 0
        # note: Arduino sketch centers y so positive -> UP in your code
        if y > 0:
            return "UP"
        if y < 0:
            return "DOWN"
        if x > 0:
            return "RIGHT"
        if x < 0:
            return "LEFT"
        return None

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass
