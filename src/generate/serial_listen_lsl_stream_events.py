import time
import threading

import serial
from pylsl import StreamInfo, StreamOutlet, local_clock

stream_name = "SerialStrStream"
stream_type = "SerialStr"

info = StreamInfo(stream_name, stream_type, 1, 0, 'string', 'serial_str')
outlet = StreamOutlet(info)

debounce_delay = 0.05
last_debounce_time = 0.0


def handle_message(data):
    global debounce_delay, last_debounce_time
    msg = data.decode('utf-8').strip()
    now = local_clock()
    if (now - last_debounce_time) > debounce_delay:
        print(f"Received message: {msg}")
        outlet.push_sample([msg], local_clock())
        last_debounce_time = now

port = '/dev/ttyACM0'
baudrate = 115200

def read_serial():
    with serial.Serial(port, baudrate, timeout=None) as ser:  # No timeout for blocking reads
        print(f"Listening on {port} at {baudrate} baud...")
        while True:
            if ser.in_waiting > 0:
                data = ser.readline()
                if data:
                    handle_message(data)  # Process the data

# Start a new thread to handle serial reading without blocking the main thread
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

while True:
    time.sleep(1)