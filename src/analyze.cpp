#include "analyze.h"
#include <sstream>
#include <numeric>
#include <essentia/algorithmfactory.h>

using namespace essentia;
using namespace essentia::standard;

static std::vector<Real> blockAverage(const std::vector<Real>& data, size_t targetSize) {
    if (data.size() <= targetSize) return data;
    std::vector<Real> result(targetSize);
    double blockSize = static_cast<double>(data.size()) / targetSize;
    for (size_t i = 0; i < targetSize; i++) {
        size_t start = static_cast<size_t>(i * blockSize);
        size_t end = static_cast<size_t>((i + 1) * blockSize);
        if (end > data.size()) end = data.size();
        Real sum = 0;
        for (size_t j = start; j < end; j++) sum += data[j];
        result[i] = sum / (end - start);
    }
    return result;
}

std::string analyzeSong(const std::vector<Real>& audio, Real sampleRate, long timeseriesLength) {
    AlgorithmFactory& factory = AlgorithmFactory::instance();

    // Key detection
    std::unique_ptr<Algorithm> keyExtractor(factory.create("KeyExtractor",
        "sampleRate", sampleRate));
    std::string key, scale;
    Real keyStrength;
    keyExtractor->input("audio").set(audio);
    keyExtractor->output("key").set(key);
    keyExtractor->output("scale").set(scale);
    keyExtractor->output("strength").set(keyStrength);
    keyExtractor->compute();

    // BPM detection — RhythmExtractor2013 only supports 44100 Hz, resample if needed
    const std::vector<Real>* bpmAudio = &audio;
    std::vector<Real> resampledAudio;
    if (sampleRate != 44100.0) {
        size_t outSize = static_cast<size_t>(
            static_cast<double>(audio.size()) * 44100.0 / sampleRate);
        if (outSize % 2 != 0) outSize++;
        size_t inSize = audio.size();
        if (inSize % 2 != 0) inSize--;
        std::vector<Real> evenAudio(audio.begin(), audio.begin() + inSize);
        std::unique_ptr<Algorithm> resampler(factory.create("ResampleFFT",
            "inSize", static_cast<int>(inSize),
            "outSize", static_cast<int>(outSize)));
        resampler->input("input").set(evenAudio);
        resampler->output("output").set(resampledAudio);
        resampler->compute();
        bpmAudio = &resampledAudio;
    }
    std::unique_ptr<Algorithm> rhythmExtractor(factory.create("RhythmExtractor2013"));
    Real bpm, bpmConfidence;
    std::vector<Real> ticks, estimates, bpmIntervals;
    rhythmExtractor->input("signal").set(*bpmAudio);
    rhythmExtractor->output("bpm").set(bpm);
    rhythmExtractor->output("confidence").set(bpmConfidence);
    rhythmExtractor->output("ticks").set(ticks);
    rhythmExtractor->output("estimates").set(estimates);
    rhythmExtractor->output("bpmIntervals").set(bpmIntervals);
    rhythmExtractor->compute();

    // Loudness (EBU R128) — needs stereo input, duplicate mono to both channels
    std::vector<StereoSample> stereoAudio(audio.size());
    for (size_t i = 0; i < audio.size(); i++) {
        stereoAudio[i].left() = audio[i];
        stereoAudio[i].right() = audio[i];
    }
    std::unique_ptr<Algorithm> loudness(factory.create("LoudnessEBUR128",
        "hopSize", 0.1, "sampleRate", sampleRate));
    Real integratedLoudness, loudnessRange;
    std::vector<Real> momentaryLoudness, shortTermLoudness;
    loudness->input("signal").set(stereoAudio);
    loudness->output("momentaryLoudness").set(momentaryLoudness);
    loudness->output("shortTermLoudness").set(shortTermLoudness);
    loudness->output("integratedLoudness").set(integratedLoudness);
    loudness->output("loudnessRange").set(loudnessRange);
    loudness->compute();
    std::vector<Real> loudnessPoints;
    if (timeseriesLength < 0)
        loudnessPoints = momentaryLoudness;
    else if (timeseriesLength > 0)
        loudnessPoints = blockAverage(momentaryLoudness, static_cast<size_t>(timeseriesLength));

    // Spectral centroid — frame-by-frame analysis
    Real nyquist = sampleRate / 2.0;
    std::unique_ptr<Algorithm> frameCutter(factory.create("FrameCutter",
        "frameSize", 2048, "hopSize", 512));
    std::unique_ptr<Algorithm> windowing(factory.create("Windowing",
        "type", "hann"));
    std::unique_ptr<Algorithm> spectrum(factory.create("Spectrum"));
    std::unique_ptr<Algorithm> centroid(factory.create("Centroid",
        "range", nyquist));

    std::vector<Real> frame, windowedFrame, spectrumValues;
    Real centroidValue;
    frameCutter->input("signal").set(audio);
    frameCutter->output("frame").set(frame);
    windowing->input("frame").set(frame);
    windowing->output("frame").set(windowedFrame);
    spectrum->input("frame").set(windowedFrame);
    spectrum->output("spectrum").set(spectrumValues);
    centroid->input("array").set(spectrumValues);
    centroid->output("centroid").set(centroidValue);

    std::vector<Real> centroidValues;
    while (true) {
        frameCutter->compute();
        if (frame.empty()) break;
        windowing->compute();
        spectrum->compute();
        centroid->compute();
        centroidValues.push_back(centroidValue);
    }
    std::vector<Real> spectralCentroidPoints;
    if (timeseriesLength < 0)
        spectralCentroidPoints = centroidValues;
    else if (timeseriesLength > 0)
        spectralCentroidPoints = blockAverage(centroidValues, static_cast<size_t>(timeseriesLength));

    // Build JSON
    Real duration = static_cast<Real>(audio.size()) / sampleRate;
    std::ostringstream json;
    json << "{"
         << "\"duration\": " << duration
         << ", \"key\": \"" << key << "\""
         << ", \"scale\": \"" << scale << "\""
         << ", \"keyStrength\": " << keyStrength
         << ", \"bpm\": " << bpm
         << ", \"bpmConfidence\": " << bpmConfidence
         << ", \"integratedLoudness\": " << integratedLoudness
         << ", \"loudnessRange\": " << loudnessRange;
    if (timeseriesLength != 0) {
        json << ", \"loudness\": [";
        for (size_t i = 0; i < loudnessPoints.size(); i++) {
            if (i > 0) json << ", ";
            json << loudnessPoints[i];
        }
        json << "], \"spectralCentroid\": [";
        for (size_t i = 0; i < spectralCentroidPoints.size(); i++) {
            if (i > 0) json << ", ";
            json << spectralCentroidPoints[i];
        }
        json << "]";
    }
    json << "}";
    return json.str();
}
