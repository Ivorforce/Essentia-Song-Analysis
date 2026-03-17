# Essentia Song Analyzer - Claude context

## What This Project Is

A CLI program that analyzes songs.
It works by running the CLI and feeding in raw song data (floats) into stdin. The program responds by generating a JSON.

The analyzed properties are:
- Tone (Musical Key, Scale)
- Tempo (BPM)

## Tech stack

- WAF build system (`./waf`)
- Essentia (`./essentia` git submodule), a library for song analysis, using Eigen.
- Multi-platform (macOS, Windows, Linux).

## Building

```bash
python3 ./waf configure
python3 ./waf build
```

Essentia is configured automatically with `--build-static --lightweight= --fft=KISS --std=c++17`.

## Usage

Pipe binary little-endian 32-bit floats (44100 Hz mono) into stdin:

```bash
./build/song-analyzer < audio.raw
```

Outputs JSON to stdout: `{"key": "A", "scale": "minor", "keyStrength": 0.69, "bpm": 128.0, "bpmConfidence": 3.5}`

## Code Conventions

### C++

- **Classes:** PascalCase
- **Methods:** camelCase
- **Private members:** `_` prefix
- Use 4-space indentation, and avoid aligning blocks for style to avoid large git diffs on changes.
