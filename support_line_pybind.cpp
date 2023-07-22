#include <pybind11/pybind11.h>
#include "support_line.hpp"
namespace py = pybind11;

PYBIND11_MODULE(sline, m) {
    m.doc() = "support line filter algorithm";
    py::class_<SupportLine>(m, "SupportLine")
        .def(py::init<int>())
        .def("reset_support_line", &SupportLine::reset_support_line)
        .def("update_support_line", &SupportLine::update_support_line)
        .def("get_support_point", &SupportLine::get_support_point);
}