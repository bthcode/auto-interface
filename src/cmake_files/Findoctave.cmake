# - Try to find a version of Octave and headers/library required by the 
#   used compiler. It determines the right MEX-File extension and add 
#   a macro to help the build of MEX-functions.
#
# This module defines: 
#  OCTAVE_INCLUDE_DIR:         include path for mex.h, mexproto.h
#  OCTAVE_OCTINTERP_LIBRARY:   path to the library octinterp
#  OCTAVE_OCTAVE_LIBRARY:      path to the library octave
#  OCTAVE_CRUFT_LIBRARY:       path to the library cruft
#  OCTAVE_LIBRARIES:           required libraries: octinterp, octave, cruft
#  OCTAVE_CREATE_MEX:          macro to build a MEX-file
#
# The macro OCTAVE_CREATE_MEX requires in this order:
#  - function's name which will be called in Octave;
#  - C/C++ source files;
#  - third libraries required.

# Copyright (c) 2009-2011 Arnaud Barr <arnaud.barre@gmail.com>
# Redistribution and use is allowed according to the terms of the BSD license.
# For details see the accompanying COPYING-CMAKE-SCRIPTS file.

IF(OCTAVE_ROOT AND OCTAVE_INCLUDE_DIR AND OCTAVE_LIBRARIES)
   # in cache already
   SET(Octave_FIND_QUIETLY TRUE)
ENDIF(OCTAVE_ROOT AND OCTAVE_INCLUDE_DIR AND OCTAVE_LIBRARIES)

SET(OCTAVE_MEXFILE_EXT mex)

IF(WIN32)
  FILE(GLOB OCTAVE_PATHS "c:/Octave/*")
  FIND_PATH(OCTAVE_ROOT "bin/octave.exe" ${OCTAVE_PATHS})
  
  FILE(GLOB OCTAVE_INCLUDE_PATHS "${OCTAVE_ROOT}/include/octave-*/octave")
  FILE(GLOB OCTAVE_LIBRARIES_PATHS "${OCTAVE_ROOT}/lib/octave-*")

  # LIBOCTINTERP, LIBOCTAVE, LIBCRUFT names
  SET(LIBOCTINTERP "liboctinterp")
  SET(LIBOCTAVE "liboctave")
  SET(LIBCRUFT "libcruft")
ELSE(WIN32)
  # MEX files extension
  IF(APPLE)
    FILE(GLOB OCTAVE_PATHS "/Applications/Octave*")
    FIND_PATH(OCTAVE_ROOT "Contents/Resources/bin/octave" ${OCTAVE_PATHS})

    FILE(GLOB OCTAVE_INCLUDE_PATHS "${OCTAVE_ROOT}/Contents/Resources/include/octave-*/octave")
    FILE(GLOB OCTAVE_LIBRARIES_PATHS "${OCTAVE_ROOT}/Contents/Resources/lib/octave-*")

    SET(LIBOCTINTERP "liboctinterp.dylib")
    SET(LIBOCTAVE "liboctave.dylib")
    SET(LIBCRUFT "libcruft.dylib")
  ELSE(APPLE)
    SET(OCTAVE_ROOT "")
    FILE(GLOB OCTAVE_LOCAL_PATHS "/usr/local/lib/octave-*")
    FILE(GLOB OCTAVE_USR_PATHS "/usr/lib/octave/*" "/usr/lib64/octave/*")
    FILE(GLOB OCTAVE_LOCAL_INC_PATHS "/usr/local/include/octave/*" )
    FILE(GLOB OCTAVE_USR_INC_PATHS "/usr/include/octave-*/octave/")

    MESSAGE( STATUS "octave local paths: " ${OCTAVE_LOCAL_PATHS} )
    MESSAGE( STATUS "octave usr paths: " ${OCTAVE_USR_PATHS} )
    MESSAGE( STATUS "octave local inc paths: " ${OCTAVE_LOCAL_INC_PATHS} )
    MESSAGE( STATUS "octave usr inc paths: " ${OCTAVE_USR_INC_PATHS} )

    SET (OCTAVE_INCLUDE_PATHS 
      "/usr/local/include"
      "/usr/local/include/octave"
      "/usr/include"
      "/usr/include/octave"
      ${OCTAVE_LOCAL_INC_PATHS}
      ${OCTAVE_USR_INC_PATHS})
    SET (OCTAVE_LIBRARIES_PATHS
      "/usr/local/lib"
      "/usr/local/lib/octave"
      ${OCTAVE_LOCAL_PATHS}
      "/usr/lib"
      "/usr/lib/octave"
      ${OCTAVE_USR_PATHS})
      
    SET (LIBOCTINTERP "octinterp")
    SET (LIBOCTAVE "octave")
    SET (LIBCRUFT "cruft")
  ENDIF(APPLE)
ENDIF(WIN32)
  
FIND_LIBRARY(OCTAVE_OCTINTERP_LIBRARY
    ${LIBOCTINTERP}
    ${OCTAVE_LIBRARIES_PATHS} NO_DEFAULT_PATH
    )
FIND_LIBRARY(OCTAVE_OCTAVE_LIBRARY
    ${LIBOCTAVE}
    ${OCTAVE_LIBRARIES_PATHS} NO_DEFAULT_PATH
    )
FIND_LIBRARY(OCTAVE_CRUFT_LIBRARY
    ${LIBCRUFT}
    ${OCTAVE_LIBRARIES_PATHS} NO_DEFAULT_PATH
    )
FIND_PATH(OCTAVE_INCLUDE_DIR
    "mex.h"
    ${OCTAVE_INCLUDE_PATHS} NO_DEFAULT_PATH
    )

# This is common to UNIX and Win32:
SET(OCTAVE_LIBRARIES
  ${OCTAVE_OCTINTERP_LIBRARY}
  ${OCTAVE_OCTAVE_LIBRARY}
  ${OCTAVE_CRUFT_LIBRARY}  
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(Octave DEFAULT_MSG OCTAVE_ROOT OCTAVE_INCLUDE_DIR OCTAVE_OCTINTERP_LIBRARY OCTAVE_OCTAVE_LIBRARY OCTAVE_CRUFT_LIBRARY)
