import time

from pylsl import StreamInfo, StreamOutlet, local_clock
from rtmidi import MidiIn # this is package python-rtmidi
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF
from rtmidi.midiutil import open_midiinput
from mido import MidiFile, MidiTrack, Message

### Examples of useful Linux commands
## play a midi file
# wildmidi /tmp/output_recording.mid
#
## list midi input devices
# aconnect -i
#
## record to midi file
# arecordmidi -p 28:0 /tmp/output_recording.mid

file_path = "/tmp/output_recording.mid"

print("Available MIDI input ports:")
for i, port in enumerate(MidiIn().get_ports()):
    print(f"{i}: {port}")


class MidiRecorder:
    def __init__(
            self,
            on_start=None,
            on_lowest_key=None,
            on_highest_key=None,
            reset_on_lowest_key=True,
            reset_on_highest_key=True,
        ):

        self.track = MidiTrack()
        self.midi_file = MidiFile()
        self.midi_file.tracks.append(self.track)

        self.started = False

        self.on_start = on_start
        self.on_lowest_key = on_lowest_key
        self.on_highest_key = on_highest_key

        self.reset_on_lowest_key = reset_on_lowest_key
        self.reset_on_highest_key = reset_on_highest_key

    def note_on(self, message):
        """Handle 'note_on' messages and add them to the MIDI track."""
        if self.started == False:
            print("Started")
            self.last_time = time.time()
            self.started = True
            if on_start is not None:
                on_start()

        print(f"Note On: {message}")
        _status, note, velocity = message
        delta_time = int((time.time() - self.last_time) * 1000)
        self.track.append(Message('note_on', note=note, velocity=velocity, time=delta_time))
        self.last_time = time.time()

        if note == 21:
            if self.reset_on_lowest_key:
                self.started = False

            if self.on_lowest_key is not None:
                self.on_lowest_key()

        if note == 108:
            if self.reset_on_highest_key:
                self.started = False

            if self.on_highest_key is not None:
                self.on_highest_key()
            

    def note_off(self, message):
        """Handle 'note_off' messages and add them to the MIDI track."""
        print(f"Note Off: {message}")
        _status, note, velocity = message
        delta_time = int((time.time() - self.last_time) * 1000)
        self.track.append(Message('note_off', note=note, velocity=velocity, time=delta_time))
        self.last_time = time.time()

    def save(self, filename):
        """Save the recorded MIDI file."""
        self.midi_file.save(filename)
        print(f"MIDI file saved as {filename}")


if __name__ == "__main__":
    stream_name = "PianoStream"
    stream_type = "Piano"
    stream_source_id = "piano"

    lsl_info = StreamInfo(stream_name, stream_type, 1, 0, 'string', stream_source_id)
    lsl_outlet = StreamOutlet(lsl_info)

    def on_start():
        print("sending lsl message 'start'")
        lsl_outlet.push_sample(['start'], local_clock())
        
    def on_lowest_key():
        print("sending lsl message 'lowest_key'")
        lsl_outlet.push_sample(['lowest_key'], local_clock())
        
    def on_highest_key():
        print("sending lsl message 'highest_key'")
        lsl_outlet.push_sample(['highest_key'], local_clock())
        
    recorder = MidiRecorder(on_start=on_start, on_lowest_key=on_lowest_key, on_highest_key=on_highest_key)

    def midi_in_callback(event, data=None):
        message, delta_time = event

        if message[0] & 0xF0 == NOTE_ON:
            recorder.note_on(message)

        if message[0] & 0xF0 == NOTE_OFF:
            recorder.note_off(message)

    try:
        # Set up the callback function
        with open_midiinput('28:0', client_name='my_client')[0] as midi_in:
            midi_in.set_callback(midi_in_callback)

            print("Waiting for messages")
            while True:
                time.sleep(1)

    except (EOFError, KeyboardInterrupt):
        print("Bye.")

    recorder.save(file_path)
