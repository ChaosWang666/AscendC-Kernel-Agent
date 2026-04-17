#include "kernel_operator.h"
#include "kernel_operator_list_tensor_intf.h"

using namespace AscendC;

class KernelUnpack {
public:
    __aicore__ inline KernelUnpack() {}
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR y, uint32_t num,
                                 uint32_t outerSize, uint32_t innerSize, uint32_t sliceStride)
    {
        this->num = num;
        this->outerSize = outerSize;
        this->innerSize = innerSize;
        this->sliceStride = sliceStride;
        this->yListAddr = y;

        uint32_t totalLen = outerSize * innerSize * sliceStride;
        uint32_t alignedTotal = ((totalLen + 15) / 16) * 16;
        xGm.SetGlobalBuffer((__gm__ half*)x, alignedTotal);

        // UB buffer for input (load whole)
        pipe.InitBuffer(inBuf, alignedTotal * sizeof(half));
        // UB buffer for one output slice
        uint32_t sliceLen = outerSize * sliceStride;
        uint32_t alignedSlice = ((sliceLen + 15) / 16) * 16;
        if (alignedSlice < 16) alignedSlice = 16;
        pipe.InitBuffer(outBuf, alignedSlice * sizeof(half));
    }

    __aicore__ inline void Process()
    {
        // Load input once
        LocalTensor<half> inLocal = inBuf.Get<half>();
        uint32_t totalLen = outerSize * innerSize * sliceStride;
        uint32_t alignedTotal = ((totalLen + 15) / 16) * 16;
        DataCopy(inLocal, xGm[0], alignedTotal);
        PipeBarrier<PIPE_ALL>();

        LocalTensor<half> outLocal = outBuf.Get<half>();
        ListTensorDesc outListDesc((__gm__ void*)yListAddr);
        uint32_t sliceLen = outerSize * sliceStride;

        for (uint32_t j = 0; j < num; j++) {
            // Gather the j-th slice from input: for each outer i, copy sliceStride elements
            // from offset [i*innerSize*sliceStride + j*sliceStride]
            for (uint32_t i = 0; i < outerSize; i++) {
                uint32_t srcBase = i * innerSize * sliceStride + j * sliceStride;
                uint32_t dstBase = i * sliceStride;
                for (uint32_t k = 0; k < sliceStride; k++) {
                    half val = inLocal.GetValue(srcBase + k);
                    outLocal.SetValue(dstBase + k, val);
                }
            }
            PipeBarrier<PIPE_ALL>();

            __gm__ uint8_t* yAddr = (__gm__ uint8_t*)outListDesc.GetDataPtr<__gm__ uint8_t>(j);
            GlobalTensor<half> yGmJ;
            uint32_t alignedSlice = ((sliceLen + 15) / 16) * 16;
            if (alignedSlice < 16) alignedSlice = 16;
            yGmJ.SetGlobalBuffer((__gm__ half*)yAddr, alignedSlice);

            // Use DataCopyPad for exact byte length
            DataCopyExtParams copyParams;
            copyParams.blockCount = 1;
            copyParams.blockLen = sliceLen * sizeof(half);
            copyParams.srcStride = 0;
            copyParams.dstStride = 0;
            DataCopyPad(yGmJ, outLocal, copyParams);
            PipeBarrier<PIPE_ALL>();
        }
    }

private:
    TPipe pipe;
    TBuf<QuePosition::VECCALC> inBuf;
    TBuf<QuePosition::VECCALC> outBuf;
    GlobalTensor<half> xGm;
    GM_ADDR yListAddr;
    uint32_t num;
    uint32_t outerSize;
    uint32_t innerSize;
    uint32_t sliceStride;
};

extern "C" __global__ __aicore__ void unpack(GM_ADDR x, GM_ADDR y, GM_ADDR workspace, GM_ADDR tiling) {
    GET_TILING_DATA(tiling_data, tiling);
    KernelUnpack op;
    op.Init(x, y, tiling_data.num, tiling_data.outerSize,
            tiling_data.innerSize, tiling_data.sliceStride);
    op.Process();
}
