#!/bin/bash
# Auto Interface
# ==============

echo "REQUIREMENTS: octave, octave-devel, python"

# Quick Start:

### Build
#mkdir build
#pushd build
#../build.sh
#popd

### Test
#pushd test
#export LD_LIBRARY_PATH=../build:$LD_LIBRARY_PATH
#octave test_Foo.m

#exit

###################################
# NOTE: CMAKE-IFICATION IN PROGRESS
###################################
mkdir stage
pushd stage
../build.sh
popd

mkdir build
pushd build
cmake ../stage
make
popd

exit

 
octave test/test_all_types.m
octave test/test_Foo.m

Missing:
 - complex

Requirements:
 - Define Data in JSON
 - Create C/C++ Code:
     - Print
     - Serializel
     - To Props / JSON
     - From Props / JSON
     - Validate
     - Set Defaults
  - Create MEX File
     - Allocate / New MATLAB
     - Allocate / New C
     - Get C Pointer
     - Matlab to C
     - C to Matlab
     - Delete C Pointer
     - Print
     - Serialize
     - To Props / JSON
     - From Props / JSON
     - Validate
     - Set Defaults
  - Create SWIG File and Python

Design:
  - Base Types:
     - Int32
     - Uint32
     - Int64
     - Uint64
     - Uint8
     - Int8
     - Uint16
     - Int16
     - double
     - float
   - Collections:
     - vector
  - JSON Definition Structure
   - Keywords:
     - STRUCT
     - NAME
     - DESCRIPTION
     - VALID_MIN
     - VALID_MAX
     - FIELDS
     - TYPE
     - DEFAULT_VALUE
     - VECTOR
     - CONTAINTED_TYPE
     - STRUCT_TYPE


Structs of Structs:
    A field may hold a struct.  
      - type = STRUCT
      - struct type = STRUCT_TYPE
      - intended behavior: call the right method on the sub-struct

Vectors:
    A field may hold multiple items
      - type = std::vector
      - data type = CONTAINTED_TYPE
      - read props: each element will be on a new line with a [ count ] appended to the prefix

Vectors holding structs:
     - data type = STRUCT
     - struct type = STRUCT_TYPE
     - will call structs read_props method with a new [ count ] until nothing is returned
