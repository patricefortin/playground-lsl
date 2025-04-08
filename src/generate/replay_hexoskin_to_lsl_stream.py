import time
import random
import numpy as np
import mne
import scipy.io
from pylsl import StreamInfo, StreamOutlet

ecg_stream_name = "ReplayHexoskinECG"
ecg_stream_type = "ECG"

resp_stream_name = "ReplayHexoskinResp"
resp_stream_type = "Breathing"

ecg_path = "data/examples/hexoskin/record_288129/ECG_I.wav"
resp_th_path = "data/examples/hexoskin/record_288129/respiration_thoracic.wav"
resp_ab_path = "data/examples/hexoskin/record_288129/respiration_abdominal.wav"

ecg_srate, ecg_data = scipy.io.wavfile.read(ecg_path)
resp_th_srate, resp_th_data = scipy.io.wavfile.read(resp_th_path)
resp_ab_srate, resp_ab_data = scipy.io.wavfile.read(resp_ab_path)

assert resp_th_srate == resp_ab_srate
assert len(resp_th_data) == len(resp_ab_data)

resp_srate = resp_th_srate
print(resp_srate)

# Create a StreamInfo object to define the stream
ecg_info = StreamInfo(ecg_stream_name, ecg_stream_type, 1, ecg_srate, 'int16', 'hexoskin_ecg')
ecg_outlet = StreamOutlet(ecg_info)

resp_info = StreamInfo(resp_stream_name, resp_stream_type, 2, resp_srate, 'int16', 'hexoskin_resp')
resp_outlet = StreamOutlet(resp_info)

start_time = time.time()
ptr = 0

foo = 128

try:
    while True:
        elapsed_time = time.time() - start_time

        ecg_ptr = ptr * 2
        resp_ptr = ptr

        ecg_samples = ecg_data[ecg_ptr:ecg_ptr+2]
        resp_sample = [resp_th_data[resp_ptr], resp_ab_data[resp_ptr]]
        #print(data)

        # Push the data to the LSL stream
        ecg_outlet.push_sample([ecg_samples[0]])
        ecg_outlet.push_sample([ecg_samples[1]])
        resp_outlet.push_sample(resp_sample)

        # Wait for the next sample (sampling rate)
        time.sleep(1 / resp_srate)
        ptr += 1
        if ptr  == len(resp_th_data):
            ptr = 0

except KeyboardInterrupt:
    print("Streaming stopped.")






