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

Feed mono audio as binary little-endian 32-bit floats via stdin. The `--samplerate` option is required:

```bash
./build/song-analyzer --samplerate 44100 < audio.raw
./build/song-analyzer --samplerate 48000 < audio.raw
```

**Note:** 44100 Hz is the expected sample rate. Other sample rates are supported but may reduce BPM accuracy. To avoid this, resample to 44100 Hz before piping — for example with ffmpeg's `-ar 44100` flag.

Use `--timeseries-length N` to include time-series arrays in the output. By default (0), they are omitted. Use `-1` to output all raw values without resampling:

```bash
./build/song-analyzer --samplerate 44100 --timeseries-length 1000 < audio.raw
./build/song-analyzer --samplerate 44100 --timeseries-length -1 < audio.raw
```

Output:
```json
{
  "duration": 210.5,
  "key": "A",
  "scale": "minor",
  "keyStrength": 0.69,
  "bpm": 128.0,
  "bpmConfidence": 2.04,
  "integratedLoudness": -14.2,
  "loudnessRange": 7.3,
  "loudness": [-18.1, -17.5, -16.8, "..."],          // only with --timeseries-length
  "spectralCentroid": [1204.3, 1180.7, 1220.1, "..."] // only with --timeseries-length
}
```

## Tests

```bash
python3 tests.py
```

To convert from a music file (requires ffmpeg):

```bash
ffmpeg -i song.mp3 -f f32le -ac 1 -ar 44100 - | ./build/song-analyzer --samplerate 44100
```

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE). See [THIRD-PARTY-LICENSES](THIRD-PARTY-LICENSES) for third-party library licenses.

## Acknowledgments

Built with [Essentia](https://essentia.upf.edu/) — an open-source C++ library for audio analysis and music information retrieval by the [Music Technology Group](https://www.upf.edu/web/mtg/) at Universitat Pompeu Fabra.
