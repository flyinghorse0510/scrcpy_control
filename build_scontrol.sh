#!/bin/bash
g++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) remote_control_pybind.cpp scrcpy_remote_control.cpp -o scontrol$(python3-config --extension-suffix)