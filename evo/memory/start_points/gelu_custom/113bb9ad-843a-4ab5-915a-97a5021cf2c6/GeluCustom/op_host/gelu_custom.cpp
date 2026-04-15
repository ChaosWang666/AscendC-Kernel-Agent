#include "gelu_custom_tiling.h"
#include "register/op_def_registry.h"

namespace optiling {

const uint32_t BUFFER_NUM = 2;
const uint32_t UB_SIZE = 192 * 1024;      // 192KB on 910B
const uint32_t RESERVE_BYTES = 12 * 1024;  // step_14

static ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    GeluCustomTilingData* tiling = context->GetTilingData<GeluCustomTilingData>();
    uint32_t totalLength = context->GetInputShape(0)->GetOriginShape().GetShapeSize();

    // Determine dtype size
    auto dtype = context->GetInputDesc(0)->GetDataType();
    uint32_t dtypeSize = (dtype == ge::DT_FLOAT16) ? 2 : 4;

    // Alignment: 32 bytes / dtypeSize
    uint32_t alignElements = 32 / dtypeSize;  // 8 for fp32, 16 for fp16

    // Compute max elements per tile buffer based on UB budget
    // Two queues (input + output), each with BUFFER_NUM buffers
    uint32_t availableUB = UB_SIZE - RESERVE_BYTES;
    uint32_t maxBytesPerBuffer = availableUB / (2 * BUFFER_NUM);
    uint32_t maxElementsPerTile = maxBytesPerBuffer / dtypeSize;
    maxElementsPerTile = (maxElementsPerTile / alignElements) * alignElements;

    // Round down maxElementsPerTile to largest power-of-2 for clean division
    uint32_t tileLength = 1;
    while (tileLength * 2 <= maxElementsPerTile) {
        tileLength *= 2;
    }

    // Dynamic BLOCK_DIM: reduce cores for small inputs
    // Each core needs at least tileLength elements (1 tile * 1 buffer minimum)
    uint32_t blockDim = totalLength / tileLength;
    if (blockDim > 32) blockDim = 32;
    if (blockDim < 1) blockDim = 1;

    // Ensure totalLength is evenly divisible by blockDim
    while (blockDim > 1 && totalLength % blockDim != 0) {
        blockDim--;
    }

    // Verify blockLength is divisible by tileLength
    uint32_t blockLength = totalLength / blockDim;
    while (tileLength > alignElements && blockLength % tileLength != 0) {
        tileLength /= 2;
    }

    context->SetBlockDim(blockDim);
    tiling->totalLength = totalLength;
    tiling->tileLength = tileLength;

    size_t* currentWorkspace = context->GetWorkspaceSizes(1);
    currentWorkspace[0] = 0;

    return ge::GRAPH_SUCCESS;
}

} // namespace optiling

namespace ge {

static graphStatus InferShape(gert::InferShapeContext* context)
{
    const gert::Shape* x_shape = context->GetInputShape(0);
    gert::Shape* z_shape = context->GetOutputShape(0);
    *z_shape = *x_shape;
    return GRAPH_SUCCESS;
}

static graphStatus InferDataType(gert::InferDataTypeContext* context)
{
    const auto inputDataType = context->GetInputDataType(0);
    context->SetOutputDataType(0, inputDataType);
    return ge::GRAPH_SUCCESS;
}

} // namespace ge

namespace ops {

class GeluCustom : public OpDef {
public:
    explicit GeluCustom(const char* name) : OpDef(name)
    {
        this->Input("x")
            .ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND});
        this->Output("z")
            .ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND});

        this->SetInferShape(ge::InferShape)
            .SetInferDataType(ge::InferDataType);

        this->AICore()
            .SetTiling(optiling::TilingFunc)
            .AddConfig("ascend910b")
            .AddConfig("ascend910_93");
    }
};

OP_ADD(GeluCustom);

} // namespace ops
