# Essentia Song Analyzer - Claude context

## What This Project Is

A CLI program that analyzes songs.
It works by running the CLI and feeding in raw song data (floats) into stdin. The program responds by generating a JSON.

The analyzed properties are:
- Tone (Musical Key, Scale)
- Tempo (BPM)
- Loudness (EBU R128 integrated, loudness range + momentary time-series)
- Spectral Centroid (brightness time-series)

## Tech stack

- WAF build system (`./waf`)
- Essentia (`./essentia` git submodule), a library for song analysis, using Eigen.
- Multi-platform (macOS, Windows, Linux).

## Building

```bash
python3 ./waf configure
python3 ./waf build
```

Essentia is configured automatically with `--build-static --lightweight= --fft=KISS --std=c++14`.

## Usage

Pipe binary little-endian 32-bit floats (mono) into stdin. `--samplerate` is required:

```bash
./build/song-analyzer --samplerate 44100 < audio.raw
./build/song-analyzer --samplerate 48000 < audio.raw
./build/song-analyzer --samplerate 44100 --timeseries-length 1000 < audio.raw
./build/song-analyzer --samplerate 44100 --timeseries-length -1 < audio.raw   # no resampling, all raw values
```

44100 Hz is expected; other sample rates may reduce BPM accuracy.

Use `--timeseries-length N` to include time-series arrays (loudness, spectralCentroid) in the output. Default is 0 (omitted). Use -1 to output all raw values without resampling.

Outputs JSON to stdout with key, scale, BPM, integrated loudness, loudness range, and optionally time-series arrays (loudness, spectralCentroid).

## Testing

```bash
python3 tests.py
```

## Code Conventions

### C++

- **Classes:** PascalCase
- **Methods:** camelCase
- **Private members:** `_` prefix
- Use 4-space indentation, and avoid aligning blocks for style to avoid large git diffs on changes.
