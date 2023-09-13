#!/bin/bash
kernelName=$(uname)
echo ${kernelName}
if [ ${kernelName} = "Darwin" ]
then
    # Build For macOS
    echo "building [1/2]"
    g++ -O2 -Wall -shared -std=c++11 -fPIC -undefined dynamic_lookup $(python3 -m pybind11 --includes) -I/opt/homebrew/include remote_control_pybind.cpp scrcpy_remote_control.cpp -o scontrol$(python3-config --extension-suffix)
    echo "building [2/2]"
    g++ -O2 -Wall -shared -std=c++11 -fPIC -undefined dynamic_lookup $(python3 -m pybind11 --includes) -I/opt/homebrew/include support_line_pybind.cpp -o sline$(python3-config --extension-suffix)
else
    # Build For Linux
    echo "building [1/2]"
    g++ -O2 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) remote_control_pybind.cpp scrcpy_remote_control.cpp -o scontrol$(python3-config --extension-suffix)
    echo "building [2/2]"
    g++ -O2 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) support_line_pybind.cpp -o sline$(python3-config --extension-suffix)
fi
