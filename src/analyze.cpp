#include "analyze.h"
#include <sstream>
#include <essentia/algorithmfactory.h>

using namespace essentia;
using namespace essentia::standard;

std::string analyzeSong(const std::vector<Real>& audio) {
    AlgorithmFactory& factory = AlgorithmFactory::instance();

    // Key detection
    std::unique_ptr<Algorithm> keyExtractor(factory.create("KeyExtractor"));
    std::string key, scale;
    Real keyStrength;
    keyExtractor->input("audio").set(audio);
    keyExtractor->output("key").set(key);
    keyExtractor->output("scale").set(scale);
    keyExtractor->output("strength").set(keyStrength);
    keyExtractor->compute();

    // BPM detection
    std::unique_ptr<Algorithm> rhythmExtractor(factory.create("RhythmExtractor2013"));
    Real bpm, bpmConfidence;
    std::vector<Real> ticks, estimates, bpmIntervals;
    rhythmExtractor->input("signal").set(audio);
    rhythmExtractor->output("bpm").set(bpm);
    rhythmExtractor->output("confidence").set(bpmConfidence);
    rhythmExtractor->output("ticks").set(ticks);
    rhythmExtractor->output("estimates").set(estimates);
    rhythmExtractor->output("bpmIntervals").set(bpmIntervals);
    rhythmExtractor->compute();

    // Build JSON
    std::ostringstream json;
    json << "{"
         << "\"key\": \"" << key << "\""
         << ", \"scale\": \"" << scale << "\""
         << ", \"keyStrength\": " << keyStrength
         << ", \"bpm\": " << bpm
         << ", \"bpmConfidence\": " << bpmConfidence
         << "}";
    return json.str();
}
