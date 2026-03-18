#include <iostream>
#include <cstdlib>
#include <cstring>
#include <vector>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
#include "essentia/essentia.h"
#include "analyze.h"
#include "version.h"

int main(int argc, char* argv[]) {
    essentia::Real sampleRate = 44100.0;

    for (int i = 1; i < argc; i++) {
        if (std::strcmp(argv[i], "--version") == 0) {
            std::cout << "song-analyzer " << SONG_ANALYZER_VERSION << std::endl;
            return 0;
        } else if (std::strcmp(argv[i], "--essentia-version") == 0) {
            std::cout << "essentia " << ESSENTIA_VERSION << std::endl;
            return 0;
        } else if (std::strcmp(argv[i], "--samplerate") == 0) {
            if (i + 1 >= argc) {
                std::cerr << "Missing value for --samplerate" << std::endl;
                return 1;
            }
            char* end;
            sampleRate = std::strtod(argv[++i], &end);
            if (*end != '\0' || sampleRate <= 0) {
                std::cerr << "Invalid sample rate: " << argv[i] << std::endl;
                return 1;
            }
        } else {
            std::cerr << "Unknown option: " << argv[i] << std::endl;
            return 1;
        }
    }

#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
#endif

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

    if (audio.size() < static_cast<size_t>(sampleRate)) {
        std::cerr << "Audio too short (less than 1 second)" << std::endl;
        return 1;
    }

    essentia::init();
    std::cout << analyzeSong(audio, sampleRate) << std::endl;
    essentia::shutdown();

    return 0;
}
