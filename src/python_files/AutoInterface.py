##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil




T="    "

class AutoGenerator:
    """
Code Generation System:

Usage:
  - A = AutoGenerator( basetypes_json_filename, structures_json_filename, output_directory )
  - A.create_struct_headers()
  - A.create_struct_impls()

  - Output:
     - For each structure:

      <foo>_class_def.h      - Primary Class Definition
      <foo>_class_def.cpp    
      <foo>_mat_support.h    - Matlab Support Functions
      <foo>_mat_support.cpp  
      <foo>_mex_impl.cpp     - Front-end MEX Code
  
    """
    def __init__(self, json_basetypes, json_file, output_directory ):
        self.basetypes = json.load( open( json_basetypes,  'r' ) )
        self.structs   = json.load( open( json_file, 'r' ) )
        self.out_dir   = output_directory
    # end __init__



