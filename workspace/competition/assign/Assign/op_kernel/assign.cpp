#include "kernel_operator.h"

using namespace AscendC;

constexpr int32_t BUFFER_NUM = 2;

class KernelAssign {
public:
    __aicore__ inline KernelAssign() {}
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR other, GM_ADDR tiling)
    {
        GET_TILING_DATA(tiling_data, tiling);
        this->totalLength = tiling_data.totalLength;
        this->tileLength = tiling_data.tileLength;
        this->loopCount = tiling_data.loopCount;
        this->tailLength = tiling_data.tailLength;

        // Align up for GM buffer registration (safe to over-declare)
        uint32_t alignedTotal = ((this->totalLength + 127) / 128) * 128;

        // GM tensors: other is source, x is destination (in-place)
        xGm.SetGlobalBuffer((__gm__ half*)x, alignedTotal);
        otherGm.SetGlobalBuffer((__gm__ half*)other, alignedTotal);

        // UB buffer: must fit the larger of tileLength or aligned-up tail
        uint32_t alignedTail = ((this->tailLength + 127) / 128) * 128;
        uint32_t bufSize = this->tileLength;
        if (alignedTail > bufSize) {
            bufSize = alignedTail;
        }
        // Minimum buffer size is 128 elements
        if (bufSize < 128) {
            bufSize = 128;
        }
        pipe.InitBuffer(inQueueSrc, BUFFER_NUM, bufSize * sizeof(half));
    }

    __aicore__ inline void Process()
    {
        // Process full tiles (each tileLength is already 128-aligned)
        for (int32_t i = 0; i < this->loopCount; i++) {
            CopyIn(i);
            CopyOut(i);
        }
        // Process tail
        if (this->tailLength > 0) {
            CopyInTail();
            CopyOutTail();
        }
    }

private:
    __aicore__ inline void CopyIn(int32_t loopIdx)
    {
        LocalTensor<half> srcLocal = inQueueSrc.AllocTensor<half>();
        DataCopy(srcLocal, otherGm[loopIdx * this->tileLength], this->tileLength);
        inQueueSrc.EnQue(srcLocal);
    }

    __aicore__ inline void CopyOut(int32_t loopIdx)
    {
        LocalTensor<half> srcLocal = inQueueSrc.DeQue<half>();
        DataCopy(xGm[loopIdx * this->tileLength], srcLocal, this->tileLength);
        inQueueSrc.FreeTensor(srcLocal);
    }

    __aicore__ inline void CopyInTail()
    {
        LocalTensor<half> srcLocal = inQueueSrc.AllocTensor<half>();
        // Align tail length up to 128 elements for DataCopy requirement
        uint32_t alignedTail = ((this->tailLength + 127) / 128) * 128;
        DataCopy(srcLocal, otherGm[this->loopCount * this->tileLength], alignedTail);
        inQueueSrc.EnQue(srcLocal);
    }

    __aicore__ inline void CopyOutTail()
    {
        LocalTensor<half> srcLocal = inQueueSrc.DeQue<half>();
        uint32_t alignedTail = ((this->tailLength + 127) / 128) * 128;
        DataCopy(xGm[this->loopCount * this->tileLength], srcLocal, alignedTail);
        inQueueSrc.FreeTensor(srcLocal);
    }

private:
    TPipe pipe;
    TQue<QuePosition::VECIN, BUFFER_NUM> inQueueSrc;
    GlobalTensor<half> xGm;
    GlobalTensor<half> otherGm;

    uint32_t totalLength;
    uint32_t tileLength;
    uint32_t loopCount;
    uint32_t tailLength;
};

extern "C" __global__ __aicore__ void assign(GM_ADDR x, GM_ADDR other, GM_ADDR workspace, GM_ADDR tiling) {
    KernelAssign op;
    op.Init(x, other, tiling);
    op.Process();
}
