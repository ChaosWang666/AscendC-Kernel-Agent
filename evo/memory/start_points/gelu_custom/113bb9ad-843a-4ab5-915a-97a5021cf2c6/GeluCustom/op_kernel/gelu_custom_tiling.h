#ifndef GELU_CUSTOM_TILING_H
#define GELU_CUSTOM_TILING_H
#include <cstdint>

struct GeluCustomTilingData {
    uint32_t totalLength;
    uint32_t tileLength;
};

#endif // GELU_CUSTOM_TILING_H
