import time
import random
import numpy as np
import mne
from pylsl import StreamInfo, StreamOutlet

stream_name = "ReplayNIRS"
stream_type = "NIRS"

# For testing, Data from the dataset "Dataset of parent-child hyperscanning fNIRS recordings"
# https://researchdata.ntu.edu.sg/dataset.xhtml?persistentId=doi:10.21979/N9/35DNCW
file_path = "data/examples/child/NIRS-2019-09-28_002.hdr"
raw = mne.io.read_raw_nirx(file_path, preload=True, verbose=True)
#n_channels = len(raw.info['ch_names'])
n_channels = 6
srate = raw.info['sfreq']

print(raw)

# Create a StreamInfo object to define the stream
info = StreamInfo(stream_name, stream_type, n_channels, srate, 'float32', 'myuid1234')

# Create an outlet to send data from this stream
outlet = StreamOutlet(info)

# Send random data to the stream

start_time = time.time()
raw_data = raw.get_data()
ptr = 0

try:
    while True:
        elapsed_time = time.time() - start_time

        # Generate random data (in this case, a float)
        data = raw_data[:n_channels,ptr]
        #print(data)

        # Push the data to the LSL stream
        outlet.push_sample(data)

        # Wait for the next sample (sampling rate)
        time.sleep(1 / srate)
        ptr += 1
        if ptr == raw_data.shape[0]:
            ptr = 0

except KeyboardInterrupt:
    print("Streaming stopped.")






