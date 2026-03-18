#pragma once
#include <string>
#include <vector>
#include <essentia/types.h>

std::string analyzeSong(const std::vector<essentia::Real>& audio, essentia::Real sampleRate = 44100.0, long timeseriesLength = 0);
