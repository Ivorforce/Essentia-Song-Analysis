# Essentia Song Analyzer - Claude context

## What This Project Is

A CLI program that analyzes songs.
It works by running the CLI and feeding in raw song data (floats) into stdin. The program responds by generating a JSON.

The analyzed properties are:
- Tone (Musical Key, Scale)
- Tempo (BPM)

## Tech stack

- WAF build system (`./waf`)
- Essentia (./essentia), a library for song analysis, using Eigen.
- Multi-platform (macOS, Windows, Linux).

## Code Conventions

### C++

- **Classes:** PascalCase
- **Methods:** camelCase
- **Private members:** `_` prefix
- Use 4-space indentation, and avoid aligning blocks for style to avoid large git diffs on changes.
