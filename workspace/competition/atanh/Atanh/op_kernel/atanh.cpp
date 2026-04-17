#include "kernel_operator.h"

using namespace AscendC;

constexpr int32_t BUFFER_NUM = 1;

class KernelAtanh {
public:
    __aicore__ inline KernelAtanh() {}
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR y, uint32_t totalLength,
                                 uint32_t tileLength, uint32_t loopCount,
                                 uint32_t tailLength)
    {
        this->tileLength = tileLength;
        this->loopCount = loopCount;
        this->tailLength = tailLength;

        uint32_t alignedTotal = ((totalLength + 127) / 128) * 128;
        xGm.SetGlobalBuffer((__gm__ half*)x, alignedTotal);
        yGm.SetGlobalBuffer((__gm__ half*)y, alignedTotal);

        // Each tile needs: inBuf (input), outBuf (output), tmp1Buf, tmp2Buf
        pipe.InitBuffer(inQueue, BUFFER_NUM, tileLength * sizeof(half));
        pipe.InitBuffer(outQueue, BUFFER_NUM, tileLength * sizeof(half));
        pipe.InitBuffer(tmpBuf1, tileLength * sizeof(half));
        pipe.InitBuffer(tmpBuf2, tileLength * sizeof(half));
    }

    __aicore__ inline void Process()
    {
        for (int32_t i = 0; i < loopCount; i++) {
            CopyIn(i, tileLength);
            Compute(tileLength);
            CopyOut(i, tileLength);
        }
        if (tailLength > 0) {
            uint32_t alignedTail = ((tailLength + 127) / 128) * 128;
            CopyIn(loopCount, alignedTail);
            Compute(alignedTail);
            CopyOut(loopCount, alignedTail);
        }
    }

private:
    __aicore__ inline void CopyIn(int32_t idx, uint32_t len)
    {
        LocalTensor<half> inLocal = inQueue.AllocTensor<half>();
        DataCopy(inLocal, xGm[idx * tileLength], len);
        inQueue.EnQue(inLocal);
    }

    __aicore__ inline void Compute(uint32_t len)
    {
        LocalTensor<half> inLocal = inQueue.DeQue<half>();
        LocalTensor<half> outLocal = outQueue.AllocTensor<half>();
        LocalTensor<half> tmp1 = tmpBuf1.Get<half>();
        LocalTensor<half> tmp2 = tmpBuf2.Get<half>();

        // atanh(x) = 0.5 * ln((1+x)/(1-x))
        // tmp1 = 1.0 + x
        Adds(tmp1, inLocal, half(1.0), len);
        // tmp2 = 1.0 - x = -(x - 1.0) => Adds(tmp2, inLocal, -1.0), then Muls(tmp2, tmp2, -1.0)
        // Or: Duplicate(tmp2, 1.0, len); Sub(tmp2, tmp2, inLocal, len)
        Duplicate(tmp2, half(1.0), len);
        Sub(tmp2, tmp2, inLocal, len);
        // tmp1 = (1+x) / (1-x)
        Div(tmp1, tmp1, tmp2, len);
        // tmp1 = ln(tmp1)
        Ln(outLocal, tmp1, len);
        // result = 0.5 * ln(...)
        Muls(outLocal, outLocal, half(0.5), len);

        outQueue.EnQue(outLocal);
        inQueue.FreeTensor(inLocal);
    }

    __aicore__ inline void CopyOut(int32_t idx, uint32_t len)
    {
        LocalTensor<half> outLocal = outQueue.DeQue<half>();
        DataCopy(yGm[idx * tileLength], outLocal, len);
        outQueue.FreeTensor(outLocal);
    }

    TPipe pipe;
    TQue<QuePosition::VECIN, BUFFER_NUM> inQueue;
    TQue<QuePosition::VECOUT, BUFFER_NUM> outQueue;
    TBuf<QuePosition::VECCALC> tmpBuf1, tmpBuf2;
    GlobalTensor<half> xGm;
    GlobalTensor<half> yGm;
    uint32_t tileLength;
    uint32_t loopCount;
    uint32_t tailLength;
};

extern "C" __global__ __aicore__ void atanh(GM_ADDR x, GM_ADDR y, GM_ADDR workspace, GM_ADDR tiling) {
    GET_TILING_DATA(tiling_data, tiling);
    KernelAtanh op;
    op.Init(x, y, tiling_data.totalLength, tiling_data.tileLength,
            tiling_data.loopCount, tiling_data.tailLength);
    op.Process();
}
