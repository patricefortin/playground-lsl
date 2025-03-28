# playground-lsl

Tools to explore LabStreamingLayer

## Installation

```
poetry install
```

## Create LSL streams

**With Muse**

```
muselsl stream --address DEVICE_MAC_ADDRESS --lsltime
```

**Noisy sinusoidal streams**

```
poetry run python src/generate/generate_random_lsl_stream.py
```

**Replay NIRS files**

```
poetry run python src/generate/replay_nirs_to_lsl_stream.py
```

**Regular events**

```
poetry run python src/generate/generate_random_lsl_stream_events.py
```

**Run TCP listen for events**

```
poetry run python src/generate/tcp_listen_lsl_stream_events.py
echo foo | nc localhost 8000 -v -q0
```

**Run Serial (arduino) listen for events**

See `./arduino` for code example to write to serial on pin interrupt

```
poetry run python src/generate/serial_listen_lsl_stream_events.py
```

## Launch the GUI

```
poetry run python src/plsl/__init__.py
```

## Launch with autoreload on save

The GUI

```
poetry run ./run-watch.sh
```

Signal generators

```
poetry run python src/generate/generate_random_lsl_stream.py
poetry run python src/generate/generate_random_lsl_stream_events.py
```

Generate events

```
find src/generate/ -name "generate_random_lsl_stream_events.py" | entr -r poetry run python src/generate/generate_random_lsl_stream_events.py
```

Generate noisy sinusoidal

```
find src/generate/ -name "generate_random_lsl_stream.py" | entr -r poetry run python src/generate/generate_random_lsl_stream.py
```
