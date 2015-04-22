#!/bin/bash

See docs/README.rst for detailed documents

# Gen CPP:
python src/python_files/CPP_Generator.py src/json_files/basetypes.json src/json_files/example.json cpp cpp

# Gen Python:
python src/python_files/Py_Generator.py src/json_files/basetypes.json src/json_files/example.json py 

# Gen Matlab
python src/python_files/MAT_Generator.py src/json_files/basetypes.json src/json_files/example.json mat

# Gen Sphinx Docs
python src/python_files/Doc_Generator.py src/json_files/basetypes.json src/json_files/example.json doc

# See the defaulting that happens in the autogen class
python src/python_files/AutoInterface.py src/json_files/basetypes.json src/json_files/example.json

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
