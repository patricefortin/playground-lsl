import time
import threading

import serial
from pylsl import StreamInfo, StreamOutlet, local_clock

srate = 50

stream_name = "SerialIntStream"
stream_type = "SerialInt"

n_channels = 6

info = StreamInfo(stream_name, stream_type, n_channels, srate, 'int16', 'serial_int')
outlet = StreamOutlet(info)

def handle_message(data):
    try:
        stripped = data.decode('utf-8').strip()
        print(stripped)
        if stripped is not '':
            values = [int(x) for x in stripped.split(',')]

            # If we started listening in the middle of a message, we will not have a complete reading
            if len(values) == n_channels:
                outlet.push_sample(values, local_clock())
    except:
        print(f"Failed to parse received data: {data}")
        

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