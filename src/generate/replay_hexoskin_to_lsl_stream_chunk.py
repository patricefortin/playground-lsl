import time
import random
import numpy as np
import mne
import scipy.io
from pylsl import StreamInfo, StreamOutlet, local_clock

TICK_MS = 50

stream_name_ecg = "ReplayHexoskinECG"
stream_type_ecg = "ECG"

stream_name_resp = "ReplayHexoskinResp"
stream_type_resp = "Breathing"

stream_name_acc = "ReplayHexoskinAcc"
stream_type_acc = "Accelerometer"

base_path = "data/examples/hexoskin/"
#record_path = "record_288129/"
record_path = "record_289810/"

path_ecg = f"{base_path}{record_path}ECG_I.wav"
path_resp_th = f"{base_path}{record_path}respiration_thoracic.wav"
path_resp_ab = f"{base_path}{record_path}respiration_abdominal.wav"
path_acc_x = f"{base_path}{record_path}acceleration_X.wav"
path_acc_y = f"{base_path}{record_path}acceleration_Y.wav"
path_acc_z = f"{base_path}{record_path}acceleration_Z.wav"

srate_ecg, data_ecg = scipy.io.wavfile.read(path_ecg)
srate_resp_th, data_resp_th = scipy.io.wavfile.read(path_resp_th)
srate_resp_ab, data_resp_ab = scipy.io.wavfile.read(path_resp_ab)
srate_acc_x, data_acc_x = scipy.io.wavfile.read(path_acc_x)
srate_acc_y, data_acc_y = scipy.io.wavfile.read(path_acc_y)
srate_acc_z, data_acc_z = scipy.io.wavfile.read(path_acc_z)

assert srate_resp_th == srate_resp_ab
assert len(data_resp_th) == len(data_resp_ab)

assert srate_acc_x == srate_acc_y
assert srate_acc_x == srate_acc_z
assert len(data_acc_x) == len(data_acc_y)
assert len(data_acc_x) == len(data_acc_z)

srate_resp = srate_resp_th
srate_acc = srate_acc_x

# Create a StreamInfo object to define the stream
info_ecg = StreamInfo(stream_name_ecg, stream_type_ecg, 1, srate_ecg, 'int16', 'hexoskin_ecg_chunk')
outlet_ecg = StreamOutlet(info_ecg)

info_resp = StreamInfo(stream_name_resp, stream_type_resp, 2, srate_resp, 'int16', 'hexoskin_resp_chunk')
outlet_resp = StreamOutlet(info_resp)

info_acc = StreamInfo(stream_name_acc, stream_type_acc, 3, srate_acc, 'int16', 'hexoskin_acc_chunk')
outlet_acc = StreamOutlet(info_acc)

start_time = time.time()
last_time = start_time

ptr = 0
next_ptr_ecg = 0
next_ptr_resp = 0
next_ptr_acc = 0

left_over_ecg = 0
left_over_resp = 0
left_over_acc = 0

try:
    while True:
        # Wait for the next sample (sampling rate)
        time.sleep(TICK_MS / 1000)

        now_time = time.time()
        since_last_time = now_time - last_time
        last_time = now_time

        n_elapsed_ecg = since_last_time * srate_ecg + left_over_ecg
        n_elapsed_resp = since_last_time * srate_resp + left_over_resp
        n_elapsed_acc = since_last_time * srate_acc + left_over_acc

        left_over_ecg = n_elapsed_ecg % 1
        left_over_resp = n_elapsed_resp % 1
        left_over_acc = n_elapsed_acc % 1

        n_read_ecg = int(n_elapsed_ecg)
        n_read_resp = int(n_elapsed_resp)
        n_read_acc = int(n_elapsed_acc)

        ptr_ecg = next_ptr_ecg
        ptr_resp = next_ptr_resp
        ptr_acc = next_ptr_acc

        next_ptr_ecg = ptr_ecg + n_read_ecg
        next_ptr_resp = ptr_resp + n_read_resp
        next_ptr_acc = ptr_acc + n_read_acc

        idx_ecg = np.arange(ptr_ecg, next_ptr_ecg)
        idx_ecg %= len(data_ecg)
        next_ptr_ecg %= len(data_ecg)

        idx_resp = np.arange(ptr_resp, next_ptr_resp)
        idx_resp %= len(data_resp_th)
        next_ptr_resp %= len(data_resp_th)

        idx_acc = np.arange(ptr_acc, next_ptr_acc)
        idx_acc %= len(data_acc_x)
        next_ptr_acc %= len(data_acc_x)

        chunk_ecg = np.array(data_ecg[idx_ecg])

        chunck_resp = np.array([[data_resp_th[id], data_resp_ab[id]] for id in idx_resp])

        chunck_acc = np.array([[data_acc_x[id], data_acc_y[id], data_acc_z[id]] for id in idx_acc])

        print(len(idx_ecg), len(idx_resp), len(idx_acc))

        # Push the data to the LSL stream
        outlet_ecg.push_chunk(chunk_ecg, local_clock())
        outlet_resp.push_chunk(chunck_resp, local_clock())
        outlet_acc.push_chunk(chunck_acc, local_clock())

except KeyboardInterrupt:
    print("Streaming stopped.")






