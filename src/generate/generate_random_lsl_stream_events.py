import time
import random
import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock

SLEEP_TIME = 0.5

# Define the stream name, type, and number of channels
stream_name = "RandomStrStream"
stream_type = "RandomStr"

info = StreamInfo(stream_name, stream_type, 1, 0, 'string', 'my_random_string')
outlet = StreamOutlet(info)

try:
    while True:
        #input('Press enter to send an event')
        outlet.push_sample(['foo'], local_clock())
        print('.')
        time.sleep(SLEEP_TIME)

except KeyboardInterrupt:
    print("Streaming stopped.")

