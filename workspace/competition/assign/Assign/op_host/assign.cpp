
#include "assign_tiling.h"
#include "register/op_def_registry.h"
#include "tiling/platform/platform_ascendc.h"

namespace optiling {
static ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    AssignTilingData tiling;

    // Get input shape (first input "x")
    const gert::StorageShape* x_shape = context->GetInputShape(0);
    uint32_t totalLength = 1;
    for (int i = 0; i < x_shape->GetStorageShape().GetDimNum(); i++) {
        totalLength *= x_shape->GetStorageShape().GetDim(i);
    }

    // DataCopy requires length aligned to 128 half elements (256 bytes)
    uint32_t ALIGN_NUM = 128;

    // Use single core for correctness
    // Tile size: process ALIGN_NUM elements per tile to keep UB usage small
    // and ensure every DataCopy is naturally aligned
    uint32_t tileLength = ALIGN_NUM * 8; // 1024 elements per tile

    // Ensure tileLength is aligned (it already is by construction)
    uint32_t loopCount = totalLength / tileLength;
    uint32_t tailLength = totalLength - loopCount * tileLength;

    tiling.set_totalLength(totalLength);
    tiling.set_tileLength(tileLength);
    tiling.set_loopCount(loopCount);
    tiling.set_tailLength(tailLength);

    // Single core
    context->SetBlockDim(1);

    tiling.SaveToBuffer(context->GetRawTilingData()->GetData(),
                        context->GetRawTilingData()->GetCapacity());
    context->GetRawTilingData()->SetDataSize(tiling.GetDataSize());

    return ge::GRAPH_SUCCESS;
}
}


namespace ge {
static ge::graphStatus InferShape(gert::InferShapeContext* context)
{
    // Assign is in-place: no output shape to set
    return GRAPH_SUCCESS;
}
static ge::graphStatus InferDataType(gert::InferDataTypeContext* context)
{
    // Assign is in-place: no output data type to set
    return ge::GRAPH_SUCCESS;
}
}


namespace ops {
class Assign : public OpDef {
public:
    explicit Assign(const char* name) : OpDef(name)
    {
        this->Input("x")
            .ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND})
            .UnknownShapeFormat({ge::FORMAT_ND});
        this->Input("other")
            .ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND})
            .UnknownShapeFormat({ge::FORMAT_ND});
        this->Attr("use_locking").Bool();

        this->SetInferShape(ge::InferShape).SetInferDataType(ge::InferDataType);

        this->AICore()
            .SetTiling(optiling::TilingFunc);
        this->AICore().AddConfig("ascend910_93");
    }
};

OP_ADD(Assign);
}
