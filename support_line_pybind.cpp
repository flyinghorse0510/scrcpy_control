#include <pybind11/pybind11.h>
#include "support_line.hpp"
namespace py = pybind11;

PYBIND11_MODULE(sline, m) {
    m.doc() = "support line filter algorithm";
    py::class_<SupportLine>(m, "SupportLine")
        .def(py::init<int>())
        .def("reset_support_line", &SupportLine::reset_support_line)
        .def("update_support_line", &SupportLine::update_support_line)
        .def("get_support_point", &SupportLine::get_support_point)
        .def("update_with_last_point", &SupportLine::update_with_last_point);

    py::class_<RankLine>(m, "RankLine")
        .def(py::init<int>())
        .def("reset_rank", &RankLine::reset_rank)
        .def("get_rank", &RankLine::get_rank)
        .def("update_rank", &RankLine::update_rank)
        .def("update_with_last_rank", &RankLine::update_with_last_rank);
}