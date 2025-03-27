import time
import random
import numpy as np
from pylsl import StreamInfo, StreamOutlet

# Define the stream name, type, and number of channels
stream_name = "RandomDataStream"
stream_type = "RandomData"
sampling_rate = 100
frequencies = [3, 20, 40]
num_channels = len(frequencies)
amplitude = 10
noise_amplitude = 1

# Create a StreamInfo object to define the stream
info = StreamInfo(stream_name, stream_type, num_channels, sampling_rate, 'float32', 'myuid1234')

# Create an outlet to send data from this stream
outlet = StreamOutlet(info)

# Send random data to the stream

start_time = time.time()


try:
    while True:
        elapsed_time = time.time() - start_time

        # Generate random data (in this case, a float)
        random_data = [amplitude * np.sin(2 * np.pi * frequency * elapsed_time) + random.uniform(-noise_amplitude, noise_amplitude) for frequency in frequencies]

        # Push the data to the LSL stream
        outlet.push_sample(random_data)

        # Wait for the next sample (sampling rate)
        time.sleep(1 / sampling_rate)

except KeyboardInterrupt:
    print("Streaming stopped.")






