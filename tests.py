#!/usr/bin/env python3
"""Unit tests for song-analyzer binary."""

import json
import math
import struct
import subprocess
import os
import re
import sys
import unittest

BINARY = os.path.join("build", "song-analyzer")
if sys.platform == "win32":
    BINARY += ".exe"
SAMPLE_RATE = 44100


def generate_sine(freq_hz, duration_sec, amplitude=0.5, sample_rate=SAMPLE_RATE):
    """Generate a mono sine wave as binary floats."""
    n = int(sample_rate * duration_sec)
    samples = [amplitude * math.sin(2 * math.pi * freq_hz * t / sample_rate) for t in range(n)]
    return struct.pack(f"<{n}f", *samples)


def generate_silence(duration_sec):
    """Generate silence as binary floats."""
    n = int(SAMPLE_RATE * duration_sec)
    return b"\x00" * (n * 4)


def generate_click_track(bpm, duration_sec):
    """Generate a click track (impulse at each beat) as binary floats."""
    n = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * n
    interval = 60.0 / bpm * SAMPLE_RATE
    pos = 0.0
    while int(pos) < n:
        samples[int(pos)] = 1.0
        pos += interval
    return struct.pack(f"<{n}f", *samples)


def run_analyzer(audio_bytes, sample_rate=SAMPLE_RATE, timeseries_length=None):
    """Run song-analyzer with given stdin bytes, return (returncode, stdout, stderr)."""
    cmd = [BINARY]
    if sample_rate != 44100:
        cmd += ["--samplerate", str(sample_rate)]
    if timeseries_length is not None:
        cmd += ["--timeseries-length", str(timeseries_length)]
    result = subprocess.run(
        cmd, input=audio_bytes,
        capture_output=True, timeout=60,
    )
    return result.returncode, result.stdout.decode(), result.stderr.decode()


class TestSongAnalyzer(unittest.TestCase):

    def test_version_flag(self):
        """--version should print version and exit successfully."""
        result = subprocess.run(
            [BINARY, "--version"],
            capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        output = result.stdout.decode().strip()
        self.assertRegex(output, r'^song-analyzer \d+\.\d+\.\d+$')

    def test_essentia_version_flag(self):
        """--essentia-version should print Essentia version and exit successfully."""
        result = subprocess.run(
            [BINARY, "--essentia-version"],
            capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("essentia", result.stdout.decode())

    def test_duration(self):
        """Duration should match the length of the input audio."""
        audio = generate_sine(440, 10)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertAlmostEqual(data["duration"], 10.0, delta=0.1)

    def test_empty_input_fails(self):
        """No audio data should exit with error."""
        code, stdout, stderr = run_analyzer(b"")
        self.assertNotEqual(code, 0)
        self.assertIn("Audio too short", stderr)

    def test_output_is_valid_json(self):
        """Output should be parseable JSON with all expected fields."""
        audio = generate_sine(440, 10)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        for field in ("duration", "key", "scale", "keyStrength", "bpm", "bpmConfidence"):
            self.assertIn(field, data)

    def test_sine_440_detects_key_a(self):
        """A 440 Hz sine wave should be detected as key A."""
        audio = generate_sine(440, 10)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["key"], "A")

    def test_sine_262_detects_key_c(self):
        """A 262 Hz sine wave (middle C) should be detected as key C."""
        audio = generate_sine(261.63, 10)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["key"], "C")

    def test_silence_does_not_crash(self):
        """Silence should produce valid JSON without crashing."""
        audio = generate_silence(5)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertIn("key", data)

    def test_click_track_detects_bpm(self):
        """A 120 BPM click track should detect BPM close to 120."""
        audio = generate_click_track(120, 30)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertAlmostEqual(data["bpm"], 120, delta=5)


    def test_loudness_fields_present(self):
        """Output should contain loudness and spectral centroid fields when requested."""
        audio = generate_sine(440, 10)
        code, stdout, _ = run_analyzer(audio, timeseries_length=1000)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        for field in ("integratedLoudness", "loudness", "spectralCentroid"):
            self.assertIn(field, data)

    def test_loudness_array_length(self):
        """Loudness and spectralCentroid arrays should have at most 1000 elements."""
        audio = generate_sine(440, 30)
        code, stdout, _ = run_analyzer(audio, timeseries_length=1000)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertLessEqual(len(data["loudness"]), 1000)
        self.assertLessEqual(len(data["spectralCentroid"]), 1000)

    def test_silence_loudness(self):
        """Silence should have very low integrated loudness (< -50 LUFS)."""
        audio = generate_silence(5)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertLess(data["integratedLoudness"], -50)

    def test_loud_vs_quiet(self):
        """A loud sine should have higher integratedLoudness than a quiet one."""
        loud = generate_sine(440, 10, amplitude=0.9)
        quiet = generate_sine(440, 10, amplitude=0.01)
        _, loud_out, _ = run_analyzer(loud)
        _, quiet_out, _ = run_analyzer(quiet)
        loud_data = json.loads(loud_out)
        quiet_data = json.loads(quiet_out)
        self.assertGreater(loud_data["integratedLoudness"], quiet_data["integratedLoudness"])

    def test_48000_sample_rate(self):
        """A 440 Hz sine at 48000 Hz should still detect key A."""
        audio = generate_sine(440, 10, sample_rate=48000)
        code, stdout, _ = run_analyzer(audio, sample_rate=48000)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["key"], "A")

    def test_spectral_centroid_sine(self):
        """A 440 Hz sine should have spectral centroid values near 440 Hz."""
        audio = generate_sine(440, 10)
        code, stdout, _ = run_analyzer(audio, timeseries_length=1000)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        centroids = data["spectralCentroid"]
        self.assertTrue(len(centroids) > 0)
        avg_centroid = sum(centroids) / len(centroids)
        self.assertAlmostEqual(avg_centroid, 440, delta=50)


    def test_timeseries_length_zero_no_arrays(self):
        """Default (0) should omit loudness and spectralCentroid keys."""
        audio = generate_sine(440, 10)
        code, stdout, _ = run_analyzer(audio, timeseries_length=0)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertNotIn("loudness", data)
        self.assertNotIn("spectralCentroid", data)

    def test_timeseries_length_minus_one_raw_values(self):
        """--timeseries-length -1 should output all raw values without resampling."""
        audio = generate_sine(440, 30)
        code_raw, stdout_raw, _ = run_analyzer(audio, timeseries_length=-1)
        self.assertEqual(code_raw, 0)
        raw = json.loads(stdout_raw)
        code_res, stdout_res, _ = run_analyzer(audio, timeseries_length=50)
        self.assertEqual(code_res, 0)
        resampled = json.loads(stdout_res)
        # Raw arrays should be longer than resampled ones
        self.assertGreater(len(raw["loudness"]), len(resampled["loudness"]))
        self.assertGreater(len(raw["spectralCentroid"]), len(resampled["spectralCentroid"]))


if __name__ == "__main__":
    unittest.main()
