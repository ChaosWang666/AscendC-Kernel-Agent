#include "kernel_operator.h"

using namespace AscendC;

constexpr int32_t BUFFER_NUM = 1;

class KernelScale {
public:
    __aicore__ inline KernelScale() {}
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR scaleGm, GM_ADDR biasGm, GM_ADDR y,
                                 uint32_t totalLength, uint32_t scaleLength, uint32_t outerLength)
    {
        this->scaleLength = scaleLength;
        this->outerLength = outerLength;
        this->alignedScaleLen = ((scaleLength + 7) / 8) * 8;  // fp32: align to 8 elements (32B)

        uint32_t alignedTotal = ((totalLength + 7) / 8) * 8;
        xGm.SetGlobalBuffer((__gm__ float*)x, alignedTotal);
        yGm.SetGlobalBuffer((__gm__ float*)y, alignedTotal);
        sGm.SetGlobalBuffer((__gm__ float*)scaleGm, alignedScaleLen);
        bGm.SetGlobalBuffer((__gm__ float*)biasGm, alignedScaleLen);

        // Buffers: input tile, scale, bias, output tile
        pipe.InitBuffer(inQueue, BUFFER_NUM, alignedScaleLen * sizeof(float));
        pipe.InitBuffer(outQueue, BUFFER_NUM, alignedScaleLen * sizeof(float));
        pipe.InitBuffer(scaleBuf, alignedScaleLen * sizeof(float));
        pipe.InitBuffer(biasBuf, alignedScaleLen * sizeof(float));
    }

    __aicore__ inline void Process()
    {
        // Load scale and bias into UB (once)
        LocalTensor<float> scaleLocal = scaleBuf.Get<float>();
        LocalTensor<float> biasLocal = biasBuf.Get<float>();
        DataCopy(scaleLocal, sGm[0], alignedScaleLen);
        DataCopy(biasLocal, bGm[0], alignedScaleLen);
        PipeBarrier<PIPE_ALL>();

        // For each outer repetition, process one scale-length block
        for (uint32_t j = 0; j < outerLength; j++) {
            uint32_t offset = j * scaleLength;

            // CopyIn: load input tile
            LocalTensor<float> inLocal = inQueue.AllocTensor<float>();
            DataCopy(inLocal, xGm[offset], alignedScaleLen);
            inQueue.EnQue(inLocal);

            // Compute: y = x * scale + bias
            inLocal = inQueue.DeQue<float>();
            LocalTensor<float> outLocal = outQueue.AllocTensor<float>();
            Mul(outLocal, inLocal, scaleLocal, alignedScaleLen);
            Add(outLocal, outLocal, biasLocal, alignedScaleLen);
            outQueue.EnQue(outLocal);
            inQueue.FreeTensor(inLocal);

            // CopyOut
            outLocal = outQueue.DeQue<float>();
            DataCopy(yGm[offset], outLocal, alignedScaleLen);
            outQueue.FreeTensor(outLocal);
        }
    }

private:
    TPipe pipe;
    TQue<QuePosition::VECIN, BUFFER_NUM> inQueue;
    TQue<QuePosition::VECOUT, BUFFER_NUM> outQueue;
    TBuf<QuePosition::VECCALC> scaleBuf, biasBuf;
    GlobalTensor<float> xGm, yGm, sGm, bGm;
    uint32_t scaleLength;
    uint32_t outerLength;
    uint32_t alignedScaleLen;
};

extern "C" __global__ __aicore__ void scale(GM_ADDR x, GM_ADDR scale, GM_ADDR bias, GM_ADDR y, GM_ADDR workspace, GM_ADDR tiling) {
    GET_TILING_DATA(tiling_data, tiling);
    KernelScale op;
    op.Init(x, scale, bias, y, tiling_data.totalLength, tiling_data.scaleLength, tiling_data.outerLength);
    op.Process();
}
