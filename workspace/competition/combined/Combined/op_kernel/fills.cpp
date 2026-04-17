#include "kernel_operator.h"

using namespace AscendC;

constexpr int32_t BUFFER_NUM = 2;

class KernelFills {
public:
    __aicore__ inline KernelFills() {}
    __aicore__ inline void Init(GM_ADDR y, uint32_t totalLength,
                                 uint32_t tileLength, uint32_t loopCount,
                                 uint32_t tailLength, float fillValue)
    {
        this->tileLength = tileLength;
        this->loopCount = loopCount;
        this->tailLength = tailLength;
        this->fillValue = static_cast<half>(fillValue);

        uint32_t elemPerCore = loopCount * tileLength + tailLength;
        uint32_t offset = GetBlockIdx() * elemPerCore;

        // Clamp to totalLength to avoid writing beyond bounds
        uint32_t gmLen = elemPerCore;
        if (offset + gmLen > totalLength) {
            gmLen = (offset < totalLength) ? (totalLength - offset) : 0;
        }
        if (gmLen == 0) {
            this->loopCount = 0;
            this->tailLength = 0;
            return;
        }

        // We write aligned tiles (may write past totalLength but that's OK
        // because output tensor is allocated with enough space)
        yGm.SetGlobalBuffer((__gm__ half*)y + offset, elemPerCore);
        pipe.InitBuffer(outQueue, BUFFER_NUM, tileLength * sizeof(half));
    }

    __aicore__ inline void Process()
    {
        for (int32_t i = 0; i < loopCount; i++) {
            FillAndCopyOut(i, tileLength);
        }
        if (tailLength > 0) {
            FillAndCopyOut(loopCount, tailLength);
        }
    }

private:
    __aicore__ inline void FillAndCopyOut(int32_t idx, uint32_t len)
    {
        LocalTensor<half> outLocal = outQueue.AllocTensor<half>();
        // Align to 128 elements (256 bytes) for Duplicate
        uint32_t alignedLen = ((len + 127) / 128) * 128;
        Duplicate(outLocal, fillValue, alignedLen);
        outQueue.EnQue(outLocal);

        outLocal = outQueue.DeQue<half>();
        DataCopy(yGm[idx * tileLength], outLocal, alignedLen);
        outQueue.FreeTensor(outLocal);
    }

    TPipe pipe;
    TQue<QuePosition::VECOUT, BUFFER_NUM> outQueue;
    GlobalTensor<half> yGm;
    uint32_t tileLength;
    uint32_t loopCount;
    uint32_t tailLength;
    half fillValue;
};

extern "C" __global__ __aicore__ void fills(GM_ADDR x, GM_ADDR y, GM_ADDR workspace, GM_ADDR tiling) {
    GET_TILING_DATA(tiling_data, tiling);
    KernelFills op;
    op.Init(y, tiling_data.totalLength, tiling_data.tileLength,
            tiling_data.loopCount, tiling_data.tailLength, tiling_data.fillValue);
    op.Process();
}
