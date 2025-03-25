import time
import random
import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock

# Define the stream name, type, and number of channels
stream_name = "RandomStrStream"
stream_type = "RandomStr"
amplitude = 10
noise_amplitude = 5

info = StreamInfo(stream_name, stream_type, 1, 0, 'string', 'my_random_string')
outlet = StreamOutlet(info)

# Send random data to the stream

start_time = time.time()

try:
    while True:
        #input('Press enter to send an event')
        outlet.push_sample(['foo'], local_clock())
        print('.')
        time.sleep(1)

except KeyboardInterrupt:
    print("Streaming stopped.")

