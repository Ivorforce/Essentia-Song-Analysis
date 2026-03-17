#!/usr/bin/env python3
"""Unit tests for song-analyzer binary."""

import json
import math
import struct
import subprocess
import unittest

BINARY = "./build/song-analyzer"
SAMPLE_RATE = 44100


def generate_sine(freq_hz, duration_sec, amplitude=0.5):
    """Generate a mono sine wave as binary floats."""
    n = int(SAMPLE_RATE * duration_sec)
    samples = [amplitude * math.sin(2 * math.pi * freq_hz * t / SAMPLE_RATE) for t in range(n)]
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


def run_analyzer(audio_bytes):
    """Run song-analyzer with given stdin bytes, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [BINARY], input=audio_bytes,
        capture_output=True, timeout=60,
    )
    return result.returncode, result.stdout.decode(), result.stderr.decode()


class TestSongAnalyzer(unittest.TestCase):

    def test_empty_input_fails(self):
        """No audio data should exit with error."""
        code, stdout, stderr = run_analyzer(b"")
        self.assertNotEqual(code, 0)
        self.assertIn("No audio data", stderr)

    def test_output_is_valid_json(self):
        """Output should be parseable JSON with all expected fields."""
        audio = generate_sine(440, 10)
        code, stdout, _ = run_analyzer(audio)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        for field in ("key", "scale", "keyStrength", "bpm", "bpmConfidence"):
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


if __name__ == "__main__":
    unittest.main()
