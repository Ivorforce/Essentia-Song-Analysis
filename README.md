# Essentia Song Analyzer

CLI tool that analyzes musical key, tempo (BPM), loudness, and spectral centroid from raw audio. Reads binary floats from stdin, outputs JSON to stdout.

## Prerequisites

- Python 3 (for waf build system)
- C++17 compiler
- Eigen (`brew install eigen` / `apt install libeigen3-dev`)

## Build

```bash
git submodule update --init
python3 ./waf configure
python3 ./waf build
```

## Usage

Feed 44100 Hz mono audio as binary little-endian 32-bit floats via stdin:

```bash
./build/song-analyzer < audio.raw
```

Output:
```json
{
  "key": "A",
  "scale": "minor",
  "keyStrength": 0.69,
  "bpm": 128.0,
  "bpmConfidence": 2.04,
  "integratedLoudness": -14.2,
  "loudness": [-18.1, -17.5, -16.8, "... up to 1000 floats"],
  "spectralCentroid": [1204.3, 1180.7, 1220.1, "... up to 1000 floats"]
}
```

## Tests

```bash
python3 tests.py
```

To convert from a music file (requires ffmpeg):

```bash
ffmpeg -i song.mp3 -f f32le -ac 1 -ar 44100 - | ./build/song-analyzer
```
