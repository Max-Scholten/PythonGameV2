# python
# file: `controller/joystick.py`
# Here under comes the imports

class ArduinoJoystick:
    """
    Non-blocking Arduino joystick wrapper.
    - Use `poll()` each frame to update `last_data`.
    - `read_input()` returns cached data (never blocks).
    - `get_direction()` returns cardinal direction from cached sample.
    """
    # Note: Somthing is missing can you find it? And what the numbers should be?
    # Tip: See the arduino code for a hint.
    def __init__(self, port, baudrate=, deadzone=):
        # timeout=0 makes reads non-blocking
        self.ser = serial.Serial(port, baudrate, timeout=0)
        self.deadzone = deadzone
        # raw values from Arduino: x,y around 0 (centered by Arduino sketch), a,b are 0/1
        self.last_data = {"y": 0, "a": 0, "b": 0}
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
                    # The prasehing is wrong
                self.last_data = {"y": y, "a": c, "b": d}
                self.updated = True
        except Exception:
            # swallow serial errors to avoid stalling the game
            pass

    def read_input(self):
        """Convenience: poll once and return cached data (never blocks)."""


    def get_direction(self):
        """Return cached cardinal direction based on last sampled values."""
        data = self.last_data
        y = data.get("y", 0)
        # apply deadzone
        if abs(y) < self.deadzone:
            y = 0
        # note: The y is for the joystick direction.
        # Keep in mind that you use the y value for both up and down motion.
        if y > 0:
            return "UP"
        if x < 0:
            return "DOWN"
        return None

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass
