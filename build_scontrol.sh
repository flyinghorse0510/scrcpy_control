#!/bin/bash
echo "building [1/2]"
g++ -O2 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) remote_control_pybind.cpp scrcpy_remote_control.cpp -o scontrol$(python3-config --extension-suffix)
echo "building [2/2]"
g++ -O2 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) support_line_pybind.cpp -o sline$(python3-config --extension-suffix)