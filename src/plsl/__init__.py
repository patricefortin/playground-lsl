from typing import List
import sys
import os
import signal
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QScreen
from pylsl import resolve_streams, StreamInlet, StreamInfo, local_clock

## Can be run like this. Note that signal.SIGHUP is necessary to kill the window application
## In one terminal
# find src -name "*.py" | entr ./kill.sh
## In another terminal
# yes | while read i; do python src/plsl/__init__.py; done

REFRESH_EVERY_MS = 20
BUFFER_DURATION_MS = 2000
FAKE_FS_FOR_EVENTS = 100


def get_lsl_stream_desc(stream: StreamInfo, channel_id: int):
    return f"{stream.name()}({stream.hostname()}) [{stream.type()}] channel {channel_id}"

class StreamChannelGUI():
    def __init__(self, stream: StreamInfo, channel_id: int):
        self.channel_id = channel_id


        # from /usr/include/lsl_cpp.h
        #/// Data format of a channel (each transmitted sample holds an array of channels).
        #enum channel_format_t {
        #	/** For up to 24-bit precision measurements in the appropriate physical unit (e.g., microvolts).
        #	Integers from -16777216 to 16777216 are represented accurately.*/
        #	cf_float32 = 1,
        #	/// For universal numeric data as long as permitted by network & disk budget.
        #	/// The largest representable integer is 53-bit.
        #	cf_double64 = 2,
        #	/// For variable-length ASCII strings or data blobs, such as video frames, complex event
        #	/// descriptions, etc.
        #	cf_string = 3,
        #	/// For high-rate digitized formats that require 32-bit precision.
        #	/// Depends critically on meta-data to represent meaningful units.
        #	/// Useful for application event codes or other coded data.
        #	cf_int32 = 4,
        #	/// For very high rate signals (40Khz+) or consumer-grade audio (for professional audio float is
        #	/// recommended).
        #	cf_int16 = 5,
        #	/// For binary signals or other coded data. Not recommended for encoding string data.
        #	cf_int8 = 6,
        #	/// For now only for future compatibility. Support for this type is not yet exposed in all
        #	/// languages. Also, some builds of liblsl will not be able to send or receive data of this
        #	/// type.
        #	cf_int64 = 7,
        #	/// Can not be transmitted.
        #	cf_undefined = 0
        #};

        self.has_srate = True
        if stream.channel_format() == 3:
            print("got a variable rate stream")
            self.has_srate = False
        
        self.graph_widget_ts = pg.PlotWidget()
        self.graph_widget_fft = pg.PlotWidget()

        self.graph_widget_ts.setTitle(get_lsl_stream_desc(stream, channel_id))
        self.graph_widget_ts.setLabel("left", "Amplitude")
        self.graph_widget_ts.setLabel("bottom", "Time (s)")

        self.graph_widget_fft.setTitle(get_lsl_stream_desc(stream, channel_id))
        self.graph_widget_fft.setLabel("left", "Amplitude")
        self.graph_widget_fft.setLabel("bottom", "Frequency (Hz)")

        self.curve_ts = self.graph_widget_ts.plot()
        self.curve_fft = self.graph_widget_fft.plot()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.graph_widget_ts)
        self.splitter.addWidget(self.graph_widget_fft)

        self.fs = stream.nominal_srate()

        fs = self.fs
        if fs == 0:
            fs = FAKE_FS_FOR_EVENTS

        self.buffer_size = int(fs * BUFFER_DURATION_MS / 1000)
        self.data_buffer = np.zeros(self.buffer_size)

        self.samples = []


class StreamGUI():
    def __init__(self, stream: StreamInfo, layout):
        self.channel_count = stream.channel_count()
        self.stream = stream
        self.inlet = StreamInlet(stream)
        self.stream_channel_guis: List[StreamChannelGUI] = []

        for i in range(self.channel_count):
            stream_channel_gui = StreamChannelGUI(stream, i)
            self.stream_channel_guis.append(stream_channel_gui)
            layout.addWidget(stream_channel_gui.splitter)

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stream_guis: List[StreamGUI] = []

        main_widget = QWidget(self)
        layout = QVBoxLayout(main_widget)

        print("Looking for LSL stream...")
        lsl_streams = resolve_streams()
        if len(lsl_streams) == 0:
            print("No stream available")
            sys.exit(1)

        print(lsl_streams)
        for lsl_stream in lsl_streams:
            stream_gui = StreamGUI(lsl_stream, layout)
            print(f"Connected: {get_lsl_stream_desc(lsl_stream, 0)}")
            self.stream_guis.append(stream_gui)

        self.setCentralWidget(main_widget)
        self.setup_timers()

    def setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(REFRESH_EVERY_MS)
    
    def update_plot(self):
        has_data = False
        for stream_gui in self.stream_guis:
            for stream_channel_gui in stream_gui.stream_channel_guis:
                stream_channel_gui.samples = []
                if not stream_channel_gui.has_srate:
                    foo = int(FAKE_FS_FOR_EVENTS * REFRESH_EVERY_MS / 1000)
                    for i in range(foo):
                        has_data = True
                        stream_channel_gui.samples.append(0)

            while True:
                sample, timestamp = stream_gui.inlet.pull_sample(timeout=0.0) # have a 0.0 timeout to avoid blocking here
                if sample:
                    has_data = True
                    for stream_channel_gui in stream_gui.stream_channel_guis:
                        if stream_channel_gui.has_srate:
                            stream_channel_gui.samples.append(sample[stream_channel_gui.channel_id])
                        else:
                            now = local_clock()
                            delta_t = now - timestamp
                            neg_id = int(delta_t * FAKE_FS_FOR_EVENTS)

                            stream_channel_gui.samples[-neg_id] = 1
                            
                else:
                    #print(f"Nb samples: {len(samples)}")
                    break

            if has_data:
                for stream_channel_gui in stream_gui.stream_channel_guis:
                    new_data = np.array(stream_channel_gui.samples)
                    if len(new_data) == 0:
                        continue

                    stream_channel_gui.data_buffer = np.roll(stream_channel_gui.data_buffer, -len(new_data))
                    stream_channel_gui.data_buffer[-len(new_data):] = new_data

                    # time series
                    stream_channel_gui.curve_ts.setData(np.linspace(0, BUFFER_DURATION_MS / 1000, len(stream_channel_gui.data_buffer)), stream_channel_gui.data_buffer)

                    # fft
                    if stream_channel_gui.has_srate:
                        fft_result = np.fft.rfft(stream_channel_gui.data_buffer)
                        freqs = np.fft.rfftfreq(len(stream_channel_gui.data_buffer), 1/stream_channel_gui.fs)
                        magnitude = np.abs(fft_result)
                        stream_channel_gui.curve_fft.setData(freqs, magnitude)
    
if __name__ == "__main__":
    app = QApplication([])
    main = MyWindow()

    # Very useful when running in auto-reload
    main.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    # position window on right screen
    monitors = QScreen.virtualSiblings(main.screen())
    left = max([x.availableGeometry().left() for x in monitors])
    top = min([x.availableGeometry().top() for x in monitors])
    main.move(left, top)

    main.show()
    app.exec()
