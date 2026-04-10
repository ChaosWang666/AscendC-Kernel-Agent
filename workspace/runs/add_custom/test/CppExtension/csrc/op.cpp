#include <torch/library.h>
#include <torch/csrc/autograd/custom_function.h>
#include "pytorch_npu_helper.hpp"
#include <torch/extension.h>

at::Tensor add_custom_impl_npu(const at::Tensor& x, const at::Tensor& y) {
    at::Tensor result = at::empty_like(x);
    EXEC_NPU_CMD(aclnnAddCustom, x, y, result);
    return result;
}

TORCH_LIBRARY_IMPL(myops, PrivateUse1, m) {
    m.impl("add_custom", &add_custom_impl_npu);
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("add_custom", &add_custom_impl_npu, "add_custom(x, y)");
}
