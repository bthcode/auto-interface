auto-interface allows a programmer to:

  1. Define data structures using a JSON syntax
  1. Auto generate C++ classes for those structures
  1. Auto generate MATLAB MEX or Octave interfaces to those classes

It uses a very straightforward Python script to generate the code, so adding functionality is easy.

CURRENT STATUS:


  * Generates valid C++ code
  * Generates valid CMake build file ( for all but mex code )
  * Missing features:
    1. Complex data
    1. Strings
    1. Needs docs and examples