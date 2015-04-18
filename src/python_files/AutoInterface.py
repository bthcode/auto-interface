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



##################################################################################
#
# CMake Build File
#
##################################################################################

    def create_cmake_lists(self):
        ret = """
cmake_minimum_required(VERSION 2.8)

PROJECT(AutoInterfaceOut)

SET( CMAKE_VERBOSE_MAKEFILE ON )

SET( CMAKE_INSTALL_PREFIX "./install" )

SET( CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${AutoInterfaceOut_SOURCE_DIR}  ${AutoInterfaceOut_SOURCE_DIR}/cmake_local_modules )

MESSAGE( STATUS "MODULE PATH: ${CMAKE_MODULE_PATH}" )

FILE( GLOB EXEC_FILES RELATIVE ${AutoInterfaceOut_SOURCE_DIR} "exec/*.cpp"  )
FILE( GLOB C_FILES  RELATIVE ${AutoInterfaceOut_SOURCE_DIR} "src/*.cpp"  )
FILE( GLOB MEX_FILES  RELATIVE ${AutoInterfaceOut_SOURCE_DIR} "mex/*mex_impl.cpp" )
FILE( GLOB MEX_CLASS_DEF RELATIVE ${AutoInterfaceOut_SOURCE_DIR} "mex/*class_def.cpp" )
FILE( GLOB MEX_MAT_SUPPORT RELATIVE ${AutoInterfaceOut_SOURCE_DIR} "mex/*mat_support.cpp" )

SET( INC_DIR  "inc" )


########### VERBOSE DEBUG ##########
MESSAGE( STATUS "C_FILES:" )
FOREACH( loop_var ${C_FILES} )
    MESSAGE( STATUS "  ${loop_var}" )
ENDFOREACH()

MESSAGE( STATUS "EXEC_FILES:" )
FOREACH( loop_var ${EXEC_FILES} )
    MESSAGE( STATUS "  ${loop_var}" )
ENDFOREACH()

MESSAGE( STATUS "MEX_FILES:" )
FOREACH( loop_var ${MEX_FILES} )
    MESSAGE( STATUS "  ${loop_var}" )
ENDFOREACH()

MESSAGE( STATUS "MEX_MAT_SUPPORT:" )
FOREACH( loop_var ${MEX_MAT_SUPPORT} )
    MESSAGE( STATUS "  ${loop_var}" )
ENDFOREACH()

MESSAGE( STATUS "MEX_CLASS_DEF:" )
FOREACH( loop_var ${MEX_CLASS_DEF} )
    MESSAGE( STATUS "  ${loop_var}" )
ENDFOREACH()

MESSAGE( STATUS "INC_DIR    = ${INC_DIR}" )
########### VERBOSE DEBUG ##########

OPTION( BUILD_OCT "Build octave mex?" False )
OPTION( BUILD_MEX "Build MTLAB mex?" False )


INCLUDE_DIRECTORIES( ${INC_DIR} "mex" ${MATLAB_INCLUDE_DIR} )

ADD_LIBRARY( auto_interface_data SHARED ${C_FILES} )
install( TARGETS auto_interface_data DESTINATION lib )
install( TARGETS auto_interface_data DESTINATION mat )

install(DIRECTORY inc/ DESTINATION inc FILES_MATCHING PATTERN "*.h")
install(DIRECTORY src/ DESTINATION src FILES_MATCHING PATTERN "*.cpp")
install(DIRECTORY mat/ DESTINATION mat FILES_MATCHING PATTERN "*.m" )
"""
        ret = ret + '## PRINTERS, GENERATORS ##'
        for struct_name, struct_def in self.structs.items():

            ret = ret + T + '# %s\n' % ( struct_name )
            ret = ret + T + 'ADD_EXECUTABLE( print_%s exec/print_%s.cpp )\n' %( struct_name, struct_name )
            ret = ret + T + 'TARGET_LINK_LIBRARIES( print_%s auto_interface_data)\n\n' % ( struct_name )
            ret = ret + T + 'ADD_EXECUTABLE( generate_%s exec/generate_%s.cpp )\n' %( struct_name, struct_name )
            ret = ret + T + 'TARGET_LINK_LIBRARIES( generate_%s auto_interface_data)\n\n' % ( struct_name )
            ret = ret + T + 'install ( TARGETS generate_%s print_%s RUNTIME DESTINATION bin )\n' % ( struct_name, struct_name )


        ret = ret + "IF( BUILD_MEX )\n"

        ret = ret + "    find_package( matlab )\n"
        ret = ret + """
# FOR FILE IN MEX_MAT_SUPPORT AND MEXX_CLASS_DEF, set -fPIC
SET_SOURCE_FILES_PROPERTIES( ${MEX_CLASS_DEF} ${MEX_MAT_SUPPORT} PROPERTIES COMPILE_FLAGS "-fPIC" )
ADD_LIBRARY( auto_interface_mat_support SHARED ${MEX_MAT_SUPPORT} ${MEX_CLASS_DEF} mex/props_parser.cpp )
TARGET_LINK_LIBRARIES( auto_interface_mat_support ${MATLAB_LIBRARIES} )
"""

        ret = ret + 'install( TARGETS auto_interface_mat_support DESTINATION mat )\n' 



        for struct_name, struct_def in self.structs.items():

            ret = ret + T + '# %s\n' % ( struct_name )
            ret = ret + T + 'SET_SOURCE_FILES_PROPERTIES( %s COMPILE_FLAGS "-I{MATLAB_PATH}/extern/include -fPIC" )\n' %( struct_name )
            ret = ret + T + 'ADD_LIBRARY( %s_mex_impl SHARED mex/%s_mex_impl.cpp )\n' %( struct_name, struct_name )
            ret = ret + T + 'SET_TARGET_PROPERTIES( %s_mex_impl PROPERTIES PREFIX "" SUFFIX ".${MATLAB_MEX_EXTENSION}" )\n' % ( struct_name )
            ret = ret + T + 'TARGET_LINK_LIBRARIES( %s_mex_impl auto_interface_mat_support )\n\n' % ( struct_name )

            ret = ret + T + 'install ( TARGETS %s_mex_impl DESTINATION mat )\n' % ( struct_name )

        ret = ret + "ENDIF( BUILD_MEX )\n\n"
        
        ret = ret + "IF( BUILD_OCT )\n"


        ret = ret + T + "FIND_PACKAGE( octave )\n"


        ret = ret + """
# FOR FILE IN MEX_MAT_SUPPORT AND MEXX_CLASS_DEF, set -fPIC
SET_SOURCE_FILES_PROPERTIES( ${MEX_CLASS_DEF} ${MEX_MAT_SUPPORT} PROPERTIES COMPILE_FLAGS "-fPIC" )
ADD_LIBRARY( auto_interface_mat_support SHARED ${MEX_MAT_SUPPORT} ${MEX_CLASS_DEF} mex/props_parser.cpp )
SET_TARGET_PROPERTIES( auto_interface_mat_support PROPERTIES COMPILE_FLAGS "-fPIC" )
"""

        ret = ret + """
    MESSAGE( STATUS "------- OCTAVE CONFIG ----------" )
    MESSAGE( STATUS "includes: ${OCTAVE_INCLUDE_DIR}" )
    MESSAGE( STATUS "lib: ${OCTAVE_OCTAVE_LIBRARY}" )
    MESSAGE( STATUS "lib_cruft: ${OCTAVE_CRUFT_LIBRARY}" )
    MESSAGE( STATUS "lib_octinterp: ${OCTAVE_OCTINTERP_LIBRARY}" )
    SET( OCT_EXT .mex      )
    SET( OCT_DEFS "-fPIC"  )
    SET( OCT_LINK_FLAGS "" )
    SET( OCT_LIBS ${OCTAVE_OCTAVE_LIBRARY} )
    SET( OCT_LIBDIRS ${OCTAVE_LOCAL_PATHS} ${OCTAVE_USR_PATHS} )
    SET( OCT_INC_DIRS ${OCTAVE_LOCAL_INC_PATHS} ${OCTAVE_USR_INC_PATHS} )
    MESSAGE( STATUS "--------------------------------" )

"""




        ret = ret + T + "LINK_DIRECTORIES( ${OCT_LIBDIRS} )\n"
        ret = ret + T + "INCLUDE_DIRECTORIES( ${OCT_INC_DIRS} )\n"

        for struct_name, struct_def in self.structs.items():

            ret = ret + T + '# %s\n' % ( struct_name )
            ret = ret + T + 'SET_SOURCE_FILES_PROPERTIES( %s_mex_impl COMPILE_FLAGS ${OCT_DEFS} )\n' %( struct_name )
            ret = ret + T + 'ADD_LIBRARY( %s_mex_impl SHARED mex/%s_mex_impl.cpp )\n' %( struct_name, struct_name )
            ret = ret + T + 'SET_TARGET_PROPERTIES( %s_mex_impl PROPERTIES PREFIX "" SUFFIX ".mex" )\n' % ( struct_name )
            ret = ret + T + 'TARGET_LINK_LIBRARIES( %s_mex_impl auto_interface_mat_support ${OCT_LIBS} )\n\n' % ( struct_name )

        ret = ret + "ENDIF( BUILD_OCT )\n"
        


        return ret
    # end create_cmake_lists
    

##################################################################################
#
# Main Driver Functions
#
##################################################################################





# TODO: write a driver that generates complete project
