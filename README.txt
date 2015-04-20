#!/bin/bash

See docs/README.rst for detailed documents

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
- c++, python, matlab
- binary i/o for C++, Python and Matlab

###
# What doesn't:

- fixed length arrays
- ascii i/o

###
# Other todos:

- ascii i/o support? json i/o support?
   - flat vectors to flat output
- auto-generate a set of tests
- should default length be supported?
- should fixed length arrays be supported?
