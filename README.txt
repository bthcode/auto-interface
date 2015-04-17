#!/bin/bash

# Auto Interface
# ==============

# Quick Start:

###################################
# NOTE: CMAKE-IFICATION IN PROGRESS
###################################
python src/python_files/MEX_Generator.py src/json_files/basetypes.json src/json_files/example.json src/c_files/
python src/python_files/CPP_Generator.py src/json_files/basetypes.json src/json_files/example.json cpp cpp
python src/python_files/C_Generator.py src/json_files/basetypes.json src/json_files/example.json c c 
python src/python_files/Py_Generator.py src/json_files/basetypes.json src/json_files/example.json py 
python src/python_files/MAT_Generator.py src/json_files/basetypes.json src/json_files/example.json mat

###
# What Works:

- basic types
- structs
- vectors
- vector of structs
- c, c++, python, matlab

###
# What doesn't:

- binary i/o for matlab
- complex default setting
- array default setting
- fixed length arrays

###
# Other todos:

- clean up AutoInterface class - has old cruft
- decide whether to support c
- ascii i/o support?
