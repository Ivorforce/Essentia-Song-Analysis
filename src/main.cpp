#include <iostream>
#include "essentia/essentia.h"

int main() {
    essentia::init();
    std::cout << "{\"status\": \"hello world\"}" << std::endl;
    essentia::shutdown();
    return 0;
}
