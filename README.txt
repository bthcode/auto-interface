#!/bin/bash

# Auto Interface
# ==============

# Quick Start:

###################################
# NOTE: CMAKE-IFICATION IN PROGRESS
###################################
python src/python_files/CPP_Generator.py src/json_files/basetypes.json src/json_files/example.json cpp cpp
python src/python_files/Py_Generator.py src/json_files/basetypes.json src/json_files/example.json py 
python src/python_files/MAT_Generator.py src/json_files/basetypes.json src/json_files/example.json mat

###
# What Works:

- basic types
- structs
- vectors
- vector of structs
- c, c++, python, matlab
- binary i/o for C++, Python and Matlab

###
# What doesn't:

- fixed length arrays
- ascii i/o

###
# Other todos:

- clean up AutoInterface class - has old cruft
- decide whether to support c
- ascii i/o support?
- auto-generate a set of tests
- better test structure
- build system for c
