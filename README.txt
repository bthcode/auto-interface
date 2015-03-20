#!/bin/bash

# Auto Interface
# ==============

echo "REQUIREMENTS: octave, octave-devel, python"

# Quick Start:

###################################
# NOTE: CMAKE-IFICATION IN PROGRESS
###################################
python src/python_files/AutoInterface.py src/json_files/basetypes.json src/json_files/example.json stage
mkdir build
cd build
cmake ../stage
make
make install
