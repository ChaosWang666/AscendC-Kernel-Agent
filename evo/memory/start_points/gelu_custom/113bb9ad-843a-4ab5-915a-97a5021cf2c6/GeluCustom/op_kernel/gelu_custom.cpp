#include "kernel_operator.h"
#include "gelu_custom_tiling.h"

constexpr int32_t BUFFER_NUM = 2;

class KernelGelu {
public:
    __aicore__ inline KernelGelu() {}
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR z, uint32_t totalLength, uint32_t tileLength)
    {
        uint32_t blockLength = totalLength / AscendC::GetBlockNum();
        this->tileLength = tileLength;
        this->loopCount = blockLength / tileLength;

        xGm.SetGlobalBuffer((__gm__ DTYPE_X*)x + blockLength * AscendC::GetBlockIdx(),
                            blockLength);
        zGm.SetGlobalBuffer((__gm__ DTYPE_Z*)z + blockLength * AscendC::GetBlockIdx(),
                            blockLength);

        pipe.InitBuffer(inQueueX, BUFFER_NUM, tileLength * sizeof(DTYPE_X));
        pipe.InitBuffer(outQueueZ, BUFFER_NUM, tileLength * sizeof(DTYPE_Z));
    }

    __aicore__ inline void Process()
    {
        for (int32_t i = 0; i < this->loopCount; i++) {
            CopyIn(i);
            Compute(i);
            CopyOut(i);
        }
    }

private:
    __aicore__ inline void CopyIn(int32_t progress)
    {
        AscendC::LocalTensor<DTYPE_X> xLocal = inQueueX.AllocTensor<DTYPE_X>();
        AscendC::DataCopy(xLocal, xGm[progress * this->tileLength], this->tileLength);
        inQueueX.EnQue(xLocal);
    }

    __aicore__ inline void Compute(int32_t progress)
    {
        AscendC::LocalTensor<DTYPE_X> xLocal = inQueueX.DeQue<DTYPE_X>();
        AscendC::LocalTensor<DTYPE_Z> zLocal = outQueueZ.AllocTensor<DTYPE_Z>();
        AscendC::Gelu(zLocal, xLocal, this->tileLength);
        outQueueZ.EnQue<DTYPE_Z>(zLocal);
        inQueueX.FreeTensor(xLocal);
    }

    __aicore__ inline void CopyOut(int32_t progress)
    {
        AscendC::LocalTensor<DTYPE_Z> zLocal = outQueueZ.DeQue<DTYPE_Z>();
        AscendC::DataCopy(zGm[progress * this->tileLength], zLocal, this->tileLength);
        outQueueZ.FreeTensor(zLocal);
    }

private:
    AscendC::TPipe pipe;
    AscendC::TQue<AscendC::TPosition::VECIN, BUFFER_NUM> inQueueX;
    AscendC::TQue<AscendC::TPosition::VECOUT, BUFFER_NUM> outQueueZ;
    AscendC::GlobalTensor<DTYPE_X> xGm;
    AscendC::GlobalTensor<DTYPE_Z> zGm;
    uint32_t tileLength;
    int32_t loopCount;
};

extern "C" __global__ __aicore__ void gelu_custom(
    GM_ADDR x, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling)
{
    REGISTER_TILING_DEFAULT(GeluCustomTilingData);
    GET_TILING_DATA(tilingData, tiling);
    KernelGelu op;
    op.Init(x, z, tilingData.totalLength, tilingData.tileLength);
    op.Process();
}
