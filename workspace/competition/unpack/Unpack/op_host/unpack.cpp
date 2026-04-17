#include "unpack_tiling.h"
#include "register/op_def_registry.h"

namespace optiling {
static ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    UnpackTilingData tiling;

    const gert::StorageShape* x_shape = context->GetInputShape(0);
    uint32_t dimNum = x_shape->GetStorageShape().GetDimNum();

    auto attrs = context->GetAttrs();
    const int64_t* numPtr = attrs->GetAttrPointer<int64_t>(0);
    const int64_t* axisPtr = attrs->GetAttrPointer<int64_t>(1);
    int64_t numAttr = *numPtr;
    int64_t axisAttr = *axisPtr;
    int32_t axis = (axisAttr < 0) ? (int32_t)(dimNum) + (int32_t)axisAttr : (int32_t)axisAttr;

    uint32_t outerSize = 1;
    for (int32_t i = 0; i < axis; i++) {
        outerSize *= x_shape->GetStorageShape().GetDim(i);
    }
    uint32_t innerSize = x_shape->GetStorageShape().GetDim(axis);
    uint32_t sliceStride = 1;
    for (uint32_t i = axis + 1; i < dimNum; i++) {
        sliceStride *= x_shape->GetStorageShape().GetDim(i);
    }

    tiling.set_num((uint32_t)numAttr);
    tiling.set_outerSize(outerSize);
    tiling.set_innerSize(innerSize);
    tiling.set_sliceStride(sliceStride);

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
class Unpack : public OpDef {
public:
    explicit Unpack(const char* name) : OpDef(name)
    {
        this->Input("x")
            .ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND})
            .UnknownShapeFormat({ge::FORMAT_ND});
        this->Output("y")
            .ParamType(DYNAMIC)
            .DataType({ge::DT_FLOAT16})
            .Format({ge::FORMAT_ND})
            .UnknownShapeFormat({ge::FORMAT_ND});
        this->Attr("num").Int();
        this->Attr("axis").Int();

        this->SetInferShape(ge::InferShape).SetInferDataType(ge::InferDataType);

        this->AICore()
            .SetTiling(optiling::TilingFunc);
        this->AICore().AddConfig("ascend910_93");
    }
};

OP_ADD(Unpack);
}
