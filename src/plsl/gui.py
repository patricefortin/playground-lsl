from typing import List
import sys
import os
import signal
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, QLabel, QTabWidget, QPushButton, QFrame
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QScreen
from pylsl import resolve_streams, StreamInlet, StreamInfo, local_clock

## Can be run like this. Note that signal.SIGHUP is necessary to kill the window application
## In one terminal
# find src -name "*.py" | entr ./kill.sh
## In another terminal
# yes | while read i; do python src/plsl/gui.py; done

REFRESH_EVERY_MS = 20
BUFFER_DURATION_MS = 5000
PSEUDO_SRATE_FOR_EVENTS = 1000


def get_lsl_stream_desc(stream: StreamInfo, channel_id: int = None):
    label = f"{stream.name()}({stream.hostname()}) [{stream.type()}]"
    if channel_id is not None:
        label += f" channel {channel_id}"
    return label

class StreamChannel():
    def __init__(self, lsl_stream: StreamInfo, channel_id: int):
        self.channel_id = channel_id
        self.lsl_stream = lsl_stream


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

        #self.ui_plot_widget_ts.setTitle(get_lsl_stream_desc(lsl_stream, channel_id))
        self.ui_plot_widget_ts.setLabel("left", "Amplitude")
        #self.ui_plot_widget_ts.setLabel("bottom", "Time (s)")

        #self.ui_plot_widget_fft.setTitle(get_lsl_stream_desc(lsl_stream, channel_id))
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
        
    @property
    def label(self):
        return get_lsl_stream_desc(self.lsl_stream, self.channel_id)

    def add_to_layout(self, layout):
              # Create the toggle button
        base_text = get_lsl_stream_desc(self.lsl_stream, self.channel_id)
        toggle_button = QPushButton(base_text)
        toggle_button.setStyleSheet("text-align: left; padding-left: 20px; border: 5px; border-color: #ffffff; background-color: #000000; color: #ffffff")
        
        # Create the layout
        layout.addWidget(toggle_button)
        layout.addWidget(self.ui_splitter)
    
        def toggle_content():
            # Toggle the visibility of the content widget
            is_visible = self.ui_splitter.isVisible()
            self.ui_splitter.setVisible(not is_visible)
            
        toggle_button.clicked.connect(toggle_content)
    



class Stream():
    def __init__(self, lsl_stream: StreamInfo, ui_layout: QVBoxLayout):
        self.channel_count = lsl_stream.channel_count()
        self.lsl_stream = lsl_stream
        self.lsl_inlet = StreamInlet(lsl_stream)
        self.channels: List[StreamChannel] = []

        for i in range(self.channel_count):
            channel = StreamChannel(lsl_stream, i)
            self.channels.append(channel)
            channel.add_to_layout(ui_layout)
            #ui_layout.addWidget(channel.ui_splitter)

    @property
    def label(self):
        return get_lsl_stream_desc(self.lsl_stream)
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.streams: List[Stream] = []

        self.tabs = QTabWidget(self)

        tab_signals_widget = QWidget(self)
        tab_signals_layout = QVBoxLayout(tab_signals_widget)
        tab_signals_widget.setLayout(tab_signals_layout)
        tab_signals_layout.setSpacing(0)

        tab_info_widget = QLabel(self, text="Foo")
        tab_info_layout = QVBoxLayout(tab_info_widget)
        tab_info_widget.setLayout(tab_info_layout)

        self.tabs.addTab(tab_signals_widget, "Signals")
        self.tabs.addTab(tab_info_widget, "Info")

        print("Looking for LSL stream...")
        lsl_streams = resolve_streams()
        if len(lsl_streams) == 0:
            print("No LSL stream available")
            sys.exit(1)

        print(lsl_streams)
        for lsl_stream in lsl_streams:
            stream = Stream(lsl_stream, tab_signals_layout)
            print(f"Connected: {get_lsl_stream_desc(lsl_stream, 0)}")
            self.streams.append(stream)

        self.setCentralWidget(self.tabs)
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
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key.Key_PageUp:
            self.tabs.setCurrentIndex(self.tabs.currentIndex() - 1)
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key.Key_PageDown:
            self.tabs.setCurrentIndex(self.tabs.currentIndex() + 1)
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

            # read all there is
            while True:
                #sample, timestamp = stream.lsl_inlet.pull_sample(timeout=0.0) # have a 0.0 timeout to avoid blocking here
                chunk, timestamps = stream.lsl_inlet.pull_chunk(timeout=0.0) # have a 0.0 timeout to avoid blocking here
                if len(chunk) == 0:
                    break # exit while True loop

                #print(f"stream '{stream.label}' len of chunk: {len(chunk)}")

                has_data = True
                for channel in stream.channels:
                    if channel.has_srate:
                        for sample in chunk:
                            channel.samples.append(sample[channel.channel_id])
                    else:
                        now = local_clock()
                        for timestamp in timestamps:
                            delta_t = now - timestamp
                            neg_id = int(delta_t * PSEUDO_SRATE_FOR_EVENTS)

                            channel.samples[-neg_id] = 1
                            
            if not has_data:
                continue # next stream

            for channel in stream.channels:
                new_data = np.array(channel.samples)
                if len(new_data) == 0:
                    continue # next channel

                channel.data_buffer = np.roll(channel.data_buffer, -len(new_data))
                channel.data_buffer[-len(new_data):] = new_data

                # time series
                channel.ui_curve_ts.setData(np.linspace(0, BUFFER_DURATION_MS / 1000, len(channel.data_buffer)), channel.data_buffer)

                # fft
                if channel.has_srate:
                    fft_result = np.fft.rfft(channel.data_buffer)
                    freqs = np.fft.rfftfreq(len(channel.data_buffer), 1/channel.fs)
                    magnitude = np.abs(fft_result)
                    # don't display index 0 to help visibility
                    channel.ui_curve_fft.setData(freqs[1:], magnitude[1:])

# Set as global so we can relaunch the app from a shortcut
main_window = None

def relaunch_main():
    global main_window
    if main_window is not None:
        main_window.close()

    main_window = MainWindow()

    # Very useful when running in auto-reload
    main_window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    # position window on right screen
    monitors = QScreen.virtualSiblings(main_window.screen())
    left = max([x.availableGeometry().left() for x in monitors])
    top = min([x.availableGeometry().top() for x in monitors])
    main_window.move(left, top)

    main_window.showMaximized()
    
    
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
