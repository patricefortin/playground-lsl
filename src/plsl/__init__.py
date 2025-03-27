from typing import List
import sys
import os
import signal
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QScreen
from pylsl import resolve_streams, StreamInlet, StreamInfo, local_clock

## Can be run like this. Note that signal.SIGHUP is necessary to kill the window application
## In one terminal
# find src -name "*.py" | entr ./kill.sh
## In another terminal
# yes | while read i; do python src/plsl/__init__.py; done

REFRESH_EVERY_MS = 20
BUFFER_DURATION_MS = 4000
PSEUDO_SRATE_FOR_EVENTS = 1000


def get_lsl_stream_desc(stream: StreamInfo, channel_id: int):
    return f"{stream.name()}({stream.hostname()}) [{stream.type()}] channel {channel_id}"

class StreamChannel():
    def __init__(self, lsl_stream: StreamInfo, channel_id: int):
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
        #	/// languages. Also, some builds of liblsl will not be able to send or receive data of this #	/// type.
        #	cf_int64 = 7,
        #	/// Can not be transmitted.
        #	cf_undefined = 0
        #};

        self.has_srate = True
        if lsl_stream.channel_format() == 3:
            print("got a variable rate stream")
            self.has_srate = False
        
        self.ui_plot_widget_ts = pg.PlotWidget()
        self.ui_plot_widget_fft = pg.PlotWidget()

        self.ui_plot_widget_ts.setTitle(get_lsl_stream_desc(lsl_stream, channel_id))
        self.ui_plot_widget_ts.setLabel("left", "Amplitude")
        self.ui_plot_widget_ts.setLabel("bottom", "Time (s)")

        self.ui_plot_widget_fft.setTitle(get_lsl_stream_desc(lsl_stream, channel_id))
        self.ui_plot_widget_fft.setLabel("left", "Amplitude")
        self.ui_plot_widget_fft.setLabel("bottom", "Frequency (Hz)")

        self.ui_curve_ts = self.ui_plot_widget_ts.plot()
        self.ui_curve_fft = self.ui_plot_widget_fft.plot()

        self.fs = lsl_stream.nominal_srate()

        fs = self.fs
        if fs == 0:
            fs = PSEUDO_SRATE_FOR_EVENTS

        self.buffer_size = int(fs * BUFFER_DURATION_MS / 1000)
        self.data_buffer = np.zeros(self.buffer_size)

        self.samples = []

        self.ui_splitter = QSplitter(Qt.Horizontal)
        self.ui_splitter.addWidget(self.ui_plot_widget_ts)
        self.ui_splitter.addWidget(self.ui_plot_widget_fft)



class Stream():
    def __init__(self, lsl_stream: StreamInfo, ui_layout: QVBoxLayout):
        self.channel_count = lsl_stream.channel_count()
        self.lsl_stream = lsl_stream
        self.lsl_inlet = StreamInlet(lsl_stream)
        self.channels: List[StreamChannel] = []

        for i in range(self.channel_count):
            channel = StreamChannel(lsl_stream, i)
            self.channels.append(channel)
            ui_layout.addWidget(channel.ui_splitter)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.streams: List[Stream] = []

        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

        print("Looking for LSL stream...")
        lsl_streams = resolve_streams()
        if len(lsl_streams) == 0:
            print("No LSL stream available")
            sys.exit(1)

        print(lsl_streams)
        for lsl_stream in lsl_streams:
            stream = Stream(lsl_stream, main_layout)
            print(f"Connected: {get_lsl_stream_desc(lsl_stream, 0)}")
            self.streams.append(stream)

        self.setCentralWidget(main_widget)
        self.setup_timers()

    def setup_timers(self):
        self.last_run = local_clock()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(REFRESH_EVERY_MS)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            print("Escape key was pressed, reloading.")
            relaunch_main()
        else:
            print(f"Key pressed: {event.text()}")
    
    def update_plot(self):
        has_data = False
        now = local_clock()
        elapsed = now - self.last_run
        self.last_run = now

        for stream in self.streams:
            for channel in stream.channels:
                if channel.has_srate:
                    channel.samples = []
                else:
                    has_data = True
                    fill_size = PSEUDO_SRATE_FOR_EVENTS * elapsed
                    fill_size = int(round(fill_size))
                    channel.samples = [0] * fill_size

            while True:
                sample, timestamp = stream.lsl_inlet.pull_sample(timeout=0.0) # have a 0.0 timeout to avoid blocking here
                if sample:
                    has_data = True
                    for channel in stream.channels:
                        if channel.has_srate:
                            channel.samples.append(sample[channel.channel_id])
                        else:
                            now = local_clock()
                            delta_t = now - timestamp
                            neg_id = int(delta_t * PSEUDO_SRATE_FOR_EVENTS)

                            channel.samples[-neg_id] = 1
                            
                else:
                    #print(f"Nb samples: {len(samples)}")
                    break

            if has_data:
                for channel in stream.channels:
                    new_data = np.array(channel.samples)
                    if len(new_data) == 0:
                        continue

                    channel.data_buffer = np.roll(channel.data_buffer, -len(new_data))
                    channel.data_buffer[-len(new_data):] = new_data

                    # time series
                    channel.ui_curve_ts.setData(np.linspace(0, BUFFER_DURATION_MS / 1000, len(channel.data_buffer)), channel.data_buffer)

                    # fft
                    if channel.has_srate:
                        fft_result = np.fft.rfft(channel.data_buffer)
                        freqs = np.fft.rfftfreq(len(channel.data_buffer), 1/channel.fs)
                        magnitude = np.abs(fft_result)
                        channel.ui_curve_fft.setData(freqs, magnitude)

main = None

def relaunch_main():
    global main
    if main is not None:
        main.close()

    main = MainWindow()

    # Very useful when running in auto-reload
    main.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    # position window on right screen
    monitors = QScreen.virtualSiblings(main.screen())
    left = max([x.availableGeometry().left() for x in monitors])
    top = min([x.availableGeometry().top() for x in monitors])
    main.move(left, top)

    main.show()
    
    
if __name__ == "__main__":
    app = QApplication([])
    relaunch_main()
    #main = MainWindow()

    ## Very useful when running in auto-reload
    #main.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    ## position window on right screen
    #monitors = QScreen.virtualSiblings(main.screen())
    #left = max([x.availableGeometry().left() for x in monitors])
    #top = min([x.availableGeometry().top() for x in monitors])
    #main.move(left, top)

    #main.show()
    app.exec()
