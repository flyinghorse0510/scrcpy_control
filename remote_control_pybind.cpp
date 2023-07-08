#include <pybind11/pybind11.h>
#include "scrcpy_remote_control.hpp"
namespace py = pybind11;

PYBIND11_MODULE(scontrol, m) {
    m.doc() = "scrcpy remote control module";

    m.def("begin_session", &begin_session, "Begin control session");
    m.def("end_session", &end_session, "Terminate control session");
    m.def("press_screen", &press_screen, "Press screen", py::arg("x"), py::arg("y"));
    m.def("long_press_screen", &long_press_screen, "Long-press screen", py::arg("x"), py::arg("y"), py::arg("pressMilliseconds"));
    m.def("release_screen", &release_screen, "Release screen", py::arg("x"), py::arg("y"));
    m.def("long_click_screen", &long_click_screen, "Long-click screen", py::arg("x"), py::arg("y"), py::arg("pressMilliseconds"));
    m.def("move_finger", &move_finger, "Move finger", py::arg("x"), py::arg("y"));
    m.def("long_press_move_finger", &long_press_move_finger, "Long-press move finger", py::arg("beginX"), py::arg("beginY"), py::arg("endX"), py::arg("endY"), py::arg("pressMilliseconds"), py::arg("durationMilliseconds"));
}