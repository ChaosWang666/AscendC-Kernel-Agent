
#include "fills_tiling.h"
#include "register/op_def_registry.h"
#include "tiling/platform/platform_ascendc.h"


namespace optiling {
static ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    FillsTilingData tiling;

    const gert::StorageShape* x_shape = context->GetInputShape(0);
    uint32_t totalLength = 1;
    for (int i = 0; i < x_shape->GetStorageShape().GetDimNum(); i++) {
        totalLength *= x_shape->GetStorageShape().GetDim(i);
    }

    const float* valuePtr = context->GetAttrs()->GetFloat(0);
    float fillValue = valuePtr ? *valuePtr : 0.0f;

    auto ascendPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
    uint32_t coreNum = ascendPlatform.GetCoreNumAiv();
    if (coreNum == 0) coreNum = 1;

    const uint32_t ALIGN_NUM = 128; // 128 half elements = 256 bytes

    // Align total length up to ALIGN_NUM for cleaner multi-core split
    uint32_t alignedTotal = ((totalLength + ALIGN_NUM - 1) / ALIGN_NUM) * ALIGN_NUM;

    // Don't use more cores than needed
    uint32_t minElemsPerCore = ALIGN_NUM;
    uint32_t maxCores = alignedTotal / minElemsPerCore;
    if (maxCores == 0) maxCores = 1;
    if (coreNum > maxCores) coreNum = maxCores;

    // Each core handles alignedTotal/coreNum elements (already aligned)
    uint32_t elemPerCore = alignedTotal / coreNum;
    // Ensure elemPerCore is aligned
    elemPerCore = ((elemPerCore + ALIGN_NUM - 1) / ALIGN_NUM) * ALIGN_NUM;

    uint32_t ubMaxElements = 32768;
    uint32_t tileLength = ubMaxElements;
    if (tileLength > elemPerCore) {
        tileLength = elemPerCore;
    }
    tileLength = (tileLength / ALIGN_NUM) * ALIGN_NUM;
    if (tileLength == 0) tileLength = ALIGN_NUM;

    uint32_t loopCount = elemPerCore / tileLength;
    uint32_t tailLength = elemPerCore - loopCount * tileLength;

    tiling.set_totalLength(totalLength);
    tiling.set_tileLength(tileLength);
    tiling.set_loopCount(loopCount);
    tiling.set_tailLength(tailLength);
    tiling.set_fillValue(fillValue);

    tiling.SaveToBuffer(context->GetRawTilingData()->GetData(),
                        context->GetRawTilingData()->GetCapacity());
    context->GetRawTilingData()->SetDataSize(tiling.GetDataSize());
    context->SetBlockDim(coreNum);

    return ge::GRAPH_SUCCESS;
}
}


namespace ge {
static ge::graphStatus InferShape(gert::InferShapeContext* context)
{
    const gert::Shape* x_shape = context->GetInputShape(0);
    gert::Shape* y_shape = context->GetOutputShape(0);
    *y_shape = *x_shape;
    return GRAPH_SUCCESS;
}
static ge::graphStatus InferDataType(gert::InferDataTypeContext *context)
{
    const auto inputDataType = context->GetInputDataType(0);
    context->SetOutputDataType(0, inputDataType);
    return ge::GRAPH_SUCCESS;
}
}


namespace ops {
class Fills : public OpDef {
public:
    explicit Fills(const char* name) : OpDef(name)
    {
        this->Input("x")
            .ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND})
            .UnknownShapeFormat({ge::FORMAT_ND});
        this->Output("y")
            .ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND})
            .UnknownShapeFormat({ge::FORMAT_ND});
        this->Attr("value").Float();

        this->SetInferShape(ge::InferShape).SetInferDataType(ge::InferDataType);

        this->AICore()
            .SetTiling(optiling::TilingFunc);
        this->AICore().AddConfig("ascend910_93");

    }
};

OP_ADD(Fills);
}
