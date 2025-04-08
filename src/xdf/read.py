import pyxdf
import matplotlib.pyplot as plt

import mne

file_path = '/home/patrice/Documents/CurrentStudy/sub-P001/ses-S001/multimodal/sub-P001_ses-S001_task-hexoskin_run-001_multimodal.xdf'
streams, header = pyxdf.load_xdf(file_path)

# Check the data type of your stream
for stream in streams:
    print(f"Stream name: {stream['info']['name']}")
    print(f"Stream type: {stream['info']['type']}")
    #print(f"Data types: {[ts.dtype for ts in stream['time_series']]}")

plt.plot(streams[1]["time_series"]/max(streams[1]["time_series"]))
plt.show()

input("foo")

