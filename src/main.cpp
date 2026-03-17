#include <iostream>
#include <vector>
#include "essentia/essentia.h"
#include "analyze.h"

int main() {
    // Read binary floats from stdin
    std::vector<essentia::Real> audio;
    constexpr size_t bufSize = 8192;
    essentia::Real buf[bufSize];

    std::cin >> std::noskipws;
    while (std::cin.read(reinterpret_cast<char*>(buf), sizeof(buf))) {
        audio.insert(audio.end(), buf, buf + bufSize);
    }
    // Handle remaining partial read
    size_t remaining = std::cin.gcount() / sizeof(essentia::Real);
    audio.insert(audio.end(), buf, buf + remaining);

    if (audio.empty()) {
        std::cerr << "No audio data received on stdin" << std::endl;
        return 1;
    }

    essentia::init();
    std::cout << analyzeSong(audio) << std::endl;
    essentia::shutdown();

    return 0;
}
