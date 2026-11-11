import serial
import time

try:
    s = serial.Serial('COM3', 115200, timeout=1)
    # Reset ESP32 via RTS
    s.dtr = False
    s.rts = True
    time.sleep(0.1)
    s.rts = False
    time.sleep(0.1)

    print("--- RESETTING ROBOT & LISTENING ---")
    t0 = time.time()
    while time.time() - t0 < 8:
        line = s.readline()
        if line:
            print(line.decode('utf-8', errors='replace').rstrip())
    s.close()
except Exception as e:
    print("Error:", e)
