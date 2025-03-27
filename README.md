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

**Regular events**

```
poetry run python src/generate/generate_random_lsl_stream_events.py
```

**Noisy sinusoidal streams**

```
poetry run python src/generate/generate_random_lsl_stream.py
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
