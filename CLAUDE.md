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

Pipe binary little-endian 32-bit floats (mono) into stdin:

```bash
./build/song-analyzer < audio.raw
./build/song-analyzer --samplerate 48000 < audio.raw
```

Default sample rate is 44100 Hz. Use `--samplerate` for other rates.

Outputs JSON to stdout with key, scale, BPM, integrated loudness, loudness range, and time-series arrays (loudness, spectralCentroid — up to 1000 points each).

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
