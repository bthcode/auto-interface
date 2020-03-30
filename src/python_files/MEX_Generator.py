##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil

from AutoInterface import AutoGenerator



T="    "
USAGE="""
USAGE: AutoGenerator.py <basetypes json file> <class definition json file> <output directory>
"""

class MexGenerator:
    """
Code Generation System:

Usage:
  - A = MexGenerator( basetypes_json_filename, structures_json_filename, output_directory )
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
    def __init__(self, basetypes, struct_defs, output_directory ):
        self.basetypes = basetypes
        self.structs   = struct_defs
        self.out_dir   = output_directory
        self.create_directory_structure()
    # end __init__


##################################################################################
#
# Utility Functions
#
##################################################################################

    def get_dependencies_for_struct(self, struct_name):
        includes = {} # insert into a map to force unique -- probably a better way
        struct_def = self.structs[ struct_name ]
        for field in struct_def['FIELDS']:
            if field['TYPE'] == "STRUCT":
                includes[ "%s_class_def.h" % ( field['STRUCT_TYPE'] ) ] = 1
            elif  field['TYPE'] == 'VECTOR' and field['CONTAINED_TYPE'] == 'STRUCT':
                includes[ "%s_class_def.h" % ( field['STRUCT_TYPE'] ) ] = 1
        return includes.keys()
    # end get_dependencies_for_struct



    def get_mat_dependencies_for_struct(self, struct_name):
        includes = {} # insert into a map to force unique -- probably a better way
        struct_def = self.structs[ struct_name ]
        for field in struct_def['FIELDS']:
            if field['TYPE'] == "STRUCT":
                includes[ "%s_mat_support.h" % ( field['STRUCT_TYPE'] ) ] = 1
            elif  field['TYPE'] == 'VECTOR' and field['CONTAINED_TYPE'] == 'STRUCT':
                includes[ "%s_mat_support.h" % ( field['STRUCT_TYPE'] ) ] = 1
        return includes.keys()
    # end get_dependencies_for_struct

##################################################################################
#
# .m file tests
#
##################################################################################



    def create_mex_test(self, struct_name):
        ret = """% Auto generated test of {0} mex interface
    addpath(cd);

    disp( 'initializing c structures');
    ref = {0}_mex_impl(0);
    ref2 = {0}_mex_impl(0);
    ref3 = {0}_mex_impl(0);

    disp( 'setting defaults...' );
    {0}_mex_impl(6, ref );

    disp( 'copying from c to mat...' );
    foo = {0}_mex_impl( 8, ref );

    disp( 'copying from mat to new c pointer...' );
    {0}_mex_impl( 9, ref2, foo  );

    disp( 'writing binary {0}.bin...');
    {0}_mex_impl( 4, ref2, 'barf.bin' );

    disp( 'reading binary {0}.bin...');
    {0}_mex_impl( 5, ref3, '{0}.bin' );
    bar = {0}_mex_impl( 8, ref3 );

    disp( 'deleting c structures' );
    {0}_mex_impl(1, ref );
    {0}_mex_impl(1, ref2 );
    {0}_mex_impl(1, ref3 );
    disp( 'success' );
""".format( struct_name )
        return ret
    # end create_mat_test
 
    def create_mat_support( self, struct_name ):
        ret = {}
        name, impl = self.create_mat_instantiate( struct_name )
        ret[ name ] = impl
        name, impl = self.create_mat_write_binary( struct_name )
        ret[ name ] = impl
        name, impl = self.create_mat_read_binary( struct_name )
        ret[ name ] = impl

        return ret
    # end create_mat_support

    def create_mat_instantiate( self, struct_name ):
        ret = ''' function [inst] = create_{0}()
    
    % create c instance
    ref = {0}_mex_impl(0);

    % set defaults
    {0}_mex_impl(6, ref );

    % copy to mat
    inst = {0}_mex_impl( 8, ref );

    % delete the c structure
    {0}_mex_impl(1, ref );
end
'''.format( struct_name )
    
        return 'create_{0}.m'.format( struct_name ), ret
    # end create_mat_instantiate

    def create_mat_write_binary( self, struct_name ):
        ret = ''' function [] = write_binary_{0}( fname, {0}_struct )
    
    % create c instance
    ref = {0}_mex_impl(0);

    % copy mat to c
    {0}_mex_impl( 9, ref, {0}_struct  );

    % write binary
    {0}_mex_impl( 4, ref, fname );

    % delete the c structure
    {0}_mex_impl(1, ref );
end
'''.format( struct_name )
    
        return 'write_binary_{0}.m'.format( struct_name ), ret
    # end create_mat_write_binary

    def create_mat_read_binary( self, struct_name ):
        ret = ''' function [ {0}_struct ] = read_binary_{0}( fname )
    
    % create c instance
    ref = {0}_mex_impl(0);

    % reading binary 
    {0}_mex_impl( 5, ref, fname );

    % copy to matlab
    {0}_struct = {0}_mex_impl( 8, ref );

    % delete the c structure
    {0}_mex_impl(1, ref );
end
'''.format( struct_name )
    
        return 'read_binary_{0}.m'.format( struct_name ), ret

    # end create_mat_write_binary


##################################################################################
#
# MEX 
#
##################################################################################


    def create_mex_impl( self, struct_name ):
        '''Creates the MEX implementation file'''

        ret = '''#include "{0}_class_def.h"
#include "{0}_mat_support.h"
#include <mex.h>

//Now the big MEX function
void  mexFunction (int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{{
    int op_type;
    if ( nrhs < 1 )
    {{
        // print error here
        return;
    }}
    op_type = * mxGetPr( prhs[0] );
    switch( op_type ) {{
    case 0:
        init_{0}( nlhs, plhs, nrhs, prhs );
        break;
    case 1:
        destroy_{0}( nlhs, plhs, nrhs, prhs );
        break;
    case 4:
        write_binary_{0}( nlhs, plhs, nrhs, prhs );
        break;
    case 5:
        read_binary_{0}( nlhs, plhs, nrhs, prhs );
        break;
    case 6:
        set_defaults_{0}( nlhs, plhs, nrhs, prhs );
        break;
    case 8:
        {0}_cpp_to_mat( nlhs, plhs, nrhs, prhs );
        break;
    case 9:
        {0}_mat_to_cpp( nlhs, plhs, nrhs, prhs );
        break;
    default:
        // raise error and return
        break;
    }}
}}
'''.format( struct_name )

        return ret
    # end create_mex_impl


##################################################################################
#
# MATLAB Support Code
#
##################################################################################


    def create_mat_support_header( self, struct_name ):
        '''Creates the MATLAB Support Header'''

        ret = '''#ifndef {0}_MAT_SUPPORT_H
#define {0}_MAT_SUPPORT_H
#include "{0}_class_def.h"
#include <mex.h>
'''.format( struct_name )

        for header in self.get_mat_dependencies_for_struct( struct_name ):
            ret = ret + '#include "{0}"\n'.format( header )
        ret = ret + '\n'

        struct_def = self.structs[ struct_name ]

        if struct_def.has_key( "NAMESPACE" ):
            ret = ret + 'using %s::%s;\n\n' % ( struct_def['NAMESPACE'], struct_name )

        ### Define sub functions
        ret = ret + '''
/**
 * @brief Copy data stored in p to new\'d mxArray
 */
mxArray * {0}_to_mat( {0} * p_{0} );

/**
 * @brief Copy mxArray to {0} pointer
 */
void mat_to_{0}( const mxArray * pMat, {0} * p_{0}, std::size_t nth_element );

/**
 * @brief Get uint64_t matlab value from {0} pointer
 */
mxArray * {0}_pointer_to_mxArray( {0} *p );

/**
 * @brief get pointer to {0} from uint64_t stored in an mxArray
 */
{0} * {0}_pointer_from_mxArray( const mxArray * );

/**
 * @brief new a {0} and return a uint64_t handle to matlab
 */
void init_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 * @brief Delete {0} from pointer stored in matlab uint64_t
 */
void destroy_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 * @brief Copy data stored in p to new\'d mxArray
 */
void write_binary_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 * @brief Copy data stored in p to new\'d mxArray
 */
void read_binary_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 * @brief Copy data stored in p to new\'d mxArray
 */
void set_defaults_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 * @brief Copy data stored in p to new\'d mxArray
 */
void {0}_cpp_to_mat( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 * @brief Copy data stored in p to new\'d mxArray
 */ 
void {0}_mat_to_cpp( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 * @brief Do the actual data copy
 */
void {0}_to_mx_struct( {0} * p_{0}, mxArray * p_ret, std::size_t nth_element );

/**
 * @brief Allocate an mxArray for this data type
 */ 
mxArray * alloc_mx_array_for_{0}( std::size_t n_elems );

#endif'''.format( struct_name )

        ### Define
        return ret
    # end create_mat_impl




    def create_mat_support_impl( self, struct_name ):
        '''Creates the MATLAB Support Implementation'''

        ret = '''
#include "{0}_mat_support.h"
#include "{0}_class_def.h"
#include <fstream>
#include <string>
#include <string.h>
#include <mex.h>
'''.format( struct_name )

        struct_def = self.structs[ struct_name ]

        if struct_def.has_key( "NAMESPACE" ):
            ret = ret + 'using {0}::{1};\n\n'.format( struct_def['NAMESPACE'], struct_name )


        ### 
        # Main driver function for going from c to matlab
        #

        ret = ret + '''
mxArray * {0}_to_mat( {0} * p_{0} )
{{  
    // Allocate a single mx struct to hold the data
    mxArray * p_ret = alloc_mx_array_for_{0}( 1 );
    // Copy data into that mxArray
    {0}_to_mx_struct( p_{0}, p_ret, 0 );
    return p_ret;
}}'''.format( struct_name )


        ### 
        # Allocate an mx array for this data type with n_elements
        #
        ret = ret + '''
mxArray * alloc_mx_array_for_{0}( std::size_t n_elems )
{{
    //# 1. allocate the big mxArray
    const char * fields[] = {{ 
'''.format( struct_name )

        for f in struct_def['FIELDS'][:-1]:
            ret = ret + T + T + '"%s",\n' % ( f['NAME'] )

        # handle the last element differently to close the c array properly...
        ret = ret  + T + T  +'"%s" };\n\n' % ( struct_def['FIELDS'][-1]['NAME'] )

        ret = ret + '''
int ndim = 2;
mwSize dims[2] = {{1,n_elems}};
int number_of_fields = {0};
mexPrintf("calling create struct array\\n");
mxArray * p_ret = mxCreateStructArray( ndim, dims,
                                     number_of_fields, fields );
return p_ret;
}}
'''.format( len( struct_def[ 'FIELDS' ] ) )


        ### 
        # Do the actual data copy
        #
        ret = ret + 'void %s_to_mx_struct( %s * p_%s, mxArray * p_ret, std::size_t nth_element )\n' % ( struct_name, struct_name, struct_name )
        ret = ret + '{\n'
        count = 0
        for f in struct_def['FIELDS']:
            ret = ret + T + '// ---- %s -----\n' % ( f['NAME'] )
            if self.basetypes.has_key( f['TYPE'] ):
                c_type = self.basetypes[ f['TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['TYPE'] ]['MAT_TYPE']
                # 1. Create numeric array
                ret = ret + T + '{\n'
                ret = ret + T + T + 'mxArray * p_tmp;\n'
                ret = ret + T + T + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                ret = ret + T + T + '\n'
                ret = ret + T + T + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxREAL);\n' % ( mat_type )
                # 2. Get pointer
                ret = ret + T + T + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                # 3. Copy c data to that pointer
                ret = ret + T + T + 'memcpy( ptr, &(p_%s->%s), sizeof( %s ));\n' % ( struct_name, f['NAME'], c_type )
                # 4. Set the mat struct element's point to the numeric array
                ret = ret + T + T + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                ret = ret + T + '}\n\n'
            elif f['TYPE'] == "STRUCT":
                ret = ret + T + '{\n'
                ret = ret + T + T + 'mxArray * p_tmp = %s_to_mat( &(p_%s->%s) );\n' % ( f["STRUCT_TYPE"], struct_name, f['NAME'] )
                ret = ret + T + T + 'mxSetFieldByNumber( p_ret, nth_element, %s, p_tmp );\n' % ( count )
                ret = ret + T + '}\n\n'
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    c_type = self.basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['CONTAINED_TYPE'] ]['MAT_TYPE']
                    # 1. Create numeric array
                    ret = ret + T + 'if ( p_%s->%s.size() ) {\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + 'mxArray * p_tmp;\n'
                    ret = ret + T + T + 'mwSize tmp_dims[2] = { p_%s->%s.size(), 1 };\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + '\n'
                    ret = ret + T + T + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxREAL);\n' % ( mat_type )
                    # 2. Get pointer
                    ret = ret + T + T + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointer
                    ret = ret + T + T + 'memcpy( ptr, (p_%s->%s.data()), sizeof( %s ) * p_%s->%s.size());\n' % ( struct_name, f['NAME'], c_type, struct_name, f['NAME'] )
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + T + T + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + T + '}\n'
                    ret = ret + T + 'else'
                    ret = ret + T + '{ // placeholder for empty vector\n'
                    ret = ret + T + T + 'mexPrintf( "empty vector for %s\\n" );\n' % f['NAME']
                    ret = ret + T + T + 'mxArray * p_tmp;\n'
                    ret = ret + T + T + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                    ret = ret + T + T + '\n'
                    ret = ret + T + T + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxREAL);\n' % ( mat_type )
                    ret = ret + T + T + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointero       
                    ret = ret + T + T + '%s t = 0;\n' % ( c_type )
                    ret = ret + T + T + 'memcpy( ptr, &(t), sizeof( %s ));\n' % ( c_type )
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + T + T + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + T + '}\n\n'

                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + T + 'if ( p_%s->%s.size() )\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + '{\n'

                    # 1. Create an mxArray of the correct length to hold the data:
                    ret = ret + T + T + 'mxArray * p_tmp = alloc_mx_array_for_%s( p_%s->%s.size() );\n' % ( f['STRUCT_TYPE'], struct_name, f['NAME'] )

                    # 2. Use the sub-structs mat_support file to generated an mxArray pointer
                    ret = ret + T + T + 'for ( size_t i=0; i < p_%s->%s.size(); i++ )\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + '{\n'

                    ret = ret + T + T + T + '%s_to_mx_struct( &(p_%s->%s[i]), p_tmp, i );\n' % ( f["STRUCT_TYPE"], struct_name, f['NAME'] )
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + T + T + '}\n'

                    ret = ret + T + T + T + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + T + '}\n\n'
 
            else:
                ret = ret + T + 'mxSetFieldByNumber( p_ret, nth_element, %s, mxCreateString( "%s" ) );\n' % ( count, count )
            count = count + 1

        ret = ret + '}\n\n'

        ### 
        # Driver function to copy from mat to cpp
        #
        ret = ret + 'void mat_to_%s( const mxArray * pMat, %s * p_%s, std::size_t nth_element )\n{\n' % ( struct_name, struct_name, struct_name )
        ret = ret + T + '// Precondition: p_%s is assumed to be created elsewhere\n\n' % ( struct_name )
        count = 0
        for f in struct_def['FIELDS']:
            ret = ret + T + '// ------- %s -----------\n' % ( f['NAME'] )
            if self.basetypes.has_key( f['TYPE'] ):
                c_type = self.basetypes[ f['TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['TYPE'] ]['MAT_TYPE']
                # 1. Get a pointer to the right place in the mxArray
                ret = ret + T + '{\n'
                ret = ret + T + T + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                ret = ret + T + T + 'if ( p_tmp )\n'
                ret = ret + T + T + '{\n'
                ret = ret + T + T + T + 'p_{0}->{1} = mxGetScalar( p_tmp );\n'.format( struct_name, f['NAME'] )
                #ret = ret + T + T + T + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                #ret = ret + T + T + T + 'memcpy( &(p_%s->%s), ptr, sizeof( %s ) );\n' % ( struct_name, f['NAME'], c_type )
                ret = ret + T + T + '}\n'
                ret = ret + T + '}\n\n'
            elif f['TYPE'] == "STRUCT":
                ret = ret + T + '{\n'
                ret = ret + T + T + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                ret = ret + T + T + 'if ( p_tmp )\n'
                ret = ret + T + T + '{\n'
                ret = ret + T + T + T + 'mat_to_%s( p_tmp, &(p_%s->%s), 0 );\n' % ( f['STRUCT_TYPE'], struct_name, f['NAME'] )
                ret = ret + T + T + '}\n'
                ret = ret + T + '}\n\n'
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    c_type = self.basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['CONTAINED_TYPE'] ]['MAT_TYPE']
                    ret = ret + T + '{\n'
                    # 1. Clear the output vector
                    ret = ret + T + 'p_%s->%s.clear();\n' % ( struct_name, f['NAME'] )
                    # 2. Get the new array size and resize the vector
                    ret = ret + T + T + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                    ret = ret + T + T + 'if ( p_tmp )\n'
                    ret = ret + T + T + '{\n'
                    ret = ret + T + T + T + 'mwSize num_elements = mxGetNumberOfElements (p_tmp);\n'
                    ret = ret + T + T + T + 'p_%s->%s.resize( num_elements );\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + T + '// Get a raw pointer to the matlab storage\n'
                    ret = ret + T + T + T + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                    ret = ret + T + T + T + '// Copy the data into c\n'
                    ret = ret + T + T + T + 'for (size_t i=0; i < num_elements; i++ )\n'
                    ret = ret + T + T + T + '{\n'
                    ret = ret + T + T + T + T + 'p_%s->%s[ i ] = (ptr[i]);\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + T + '}\n'
                    ret = ret + T + T + '}\n'
                    ret = ret + T + '}\n\n'
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + T + '{\n'
                    # 1. Clear the output vector
                    ret = ret + T + 'p_%s->%s.clear();\n' % ( struct_name, f['NAME'] )
                    # 2. Get the new array size and resize the vector
                    ret = ret + T + T + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                    ret = ret + T + T + 'if ( p_tmp )\n'
                    ret = ret + T + T + '{\n'
                    ret = ret + T + T + T + 'mwSize num_elements = mxGetNumberOfElements (p_tmp);\n'
                    ret = ret + T + T + T + 'p_%s->%s.resize( num_elements );\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + T + '\n'
                    ret = ret + T + T + T + '// Copy the data into c\n'
                    ret = ret + T + T + T + 'for (size_t i=0; i < num_elements; i++ )\n'
                    ret = ret + T + T + T + '{\n'
                    ret = ret + T + T + T + T + 'mat_to_%s(p_tmp, &(p_%s->%s[i]), i);\n' % ( f['STRUCT_TYPE'], struct_name, f['NAME'] )
                    ret = ret + T + T + T + '}\n'
                    ret = ret + T + T + '}\n'
                    ret = ret + T + '}\n\n'
             
            count = count + 1
            # end for each field
 
        ret = ret + '}\n\n'

        ### Copy a pointer value into an mxArray
        ret = ret + 'mxArray * %s_pointer_to_mxArray( %s *p )\n{\n' % ( struct_name, struct_name )
        ret = ret + T + '// Allocate an mxArray to hold the data\n'
        ret = ret + T + 'mxArray * mxArr = mxCreateNumericMatrix( 1, 1, mxUINT64_CLASS, mxREAL );\n\n'
        ret = ret + T + '// Get a pointer to the mxArray\' data\n'
        ret = ret + T + 'uint64_t * ptr = (uint64_t*) mxGetData( mxArr );\n'
        ret = ret + T + '// Copy the pointer value\n\n'
        ret = ret + T + 'memcpy( ptr, &p, sizeof( %s * ));\n' % ( struct_name )
        ret = ret + T + 'return mxArr;\n'
        ret = ret + '}\n\n'

        ### Get a pointer value from an mxArray
        ret = ret + '%s * %s_pointer_from_mxArray( const mxArray * mxArray )\n{\n' % ( struct_name, struct_name )
        ret = ret + T + 'uint64_t * ptr = ( uint64_t * ) mxGetData( mxArray );\n' 
        ret = ret + T + 'void * p_tmp[ 2 ];\n'
        ret = ret + T + 'memcpy( ( & ( p_tmp[ 0 ] ) ), ptr, sizeof( void * ) );\n'
        ret = ret + T + '%s * ret = ( %s * )( p_tmp[ 0 ] );\n' % ( struct_name, struct_name )
        ret = ret + T + 'return ret;\n'
        ret = ret + '}\n\n'

        ### Init
        ret = ret + 'void init_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % ( struct_name )
        ret = ret + T + '// new a %s object, and send back a pointer\n' % ( struct_name )
        ret = ret + T + '%s * p = new %s;\n' % ( struct_name, struct_name );
        ret = ret + T + 'plhs[0] = %s_pointer_to_mxArray( p );\n' % ( struct_name ) 
        ret = ret + '}\n\n'

        ### Destroy
        ret = ret + 'void destroy_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % ( struct_name )
        ret = ret + T + '// destroy a %s object\n\n' % ( struct_name )
        ret = ret + T + 'if ( nrhs != 2 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'std::cout << "this is an error here..." << std::endl;\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'delete p;\n'
        ret = ret + '}\n\n'

        ### Write Binary
        ret = ret + 'void write_binary_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + T + '// call a %s object\'s write_binary\n' % ( struct_name )
        ret = ret + T + 'char * file_name;\n'
        ret = ret + T + 'int  buflen;\n'
        ret = ret + T + 'if ( nrhs != 3 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + '// copy file name and prefix into c strings\n'
        ret = ret + T + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + T + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + T + 'mxGetString(prhs[2], file_name, buflen);\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'std::ofstream of_out;\n'
        ret = ret + T + 'of_out.open( file_name, std::ios::binary );\n'
        ret = ret + T + 'p->write_binary( of_out );\n'

        ret = ret + '}\n\n'

        ### Read Binary
        ret = ret + 'void read_binary_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + T + '// call a %s object\'s read_binary\n' % ( struct_name )
        ret = ret + T + 'char * file_name;\n'
        ret = ret + T + 'int  buflen;\n'
        ret = ret + T + 'if ( nrhs != 3 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + '// copy file name and prefix into c strings\n'
        ret = ret + T + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + T + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + T + 'mxGetString(prhs[2], file_name, buflen);\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'std::ifstream if_in;\n'
        ret = ret + T + 'if_in.open( file_name, std::ios::binary );\n'
        ret = ret + T + 'p->read_binary( if_in );\n'
        ret = ret + '}\n\n'

        ### Set Defaults
        ret = ret + 'void set_defaults_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % ( struct_name )
        ret = ret + T + '// call a %s object\'s set_defaults\n' % ( struct_name )
        ret = ret + T + 'if ( nrhs != 2 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'p->set_defaults();\n'
        ret = ret + '}\n\n'

        ### Cpp to Mat
        ret = ret + 'void %s_cpp_to_mat( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + T + '// copy %s object to matlab object\n' % ( struct_name )
        ret = ret + T + 'if ( nrhs != 2 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'plhs[0] = %s_to_mat( p );\n' % ( struct_name )
        ret = ret + '}\n\n'

        ### Mat to Cpp
        ret = ret + 'void %s_mat_to_cpp( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + T + '// copy %s matlab object to cpp object\n' % ( struct_name )
        ret = ret + T + 'if ( nrhs != 3 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + 'mexPrintf("Error, not enough arguments\\n");\n'
        ret = ret + T + T + 'return;'
        ret = ret + T + '}\n\n'
        ret = ret + T + '// Copy pointer from reference\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + '// Make the call\n'
        ret = ret + T + 'mat_to_%s( prhs[2], p, 0 );\n' % ( struct_name )
        ret = ret + '}\n\n'

        return ret
    # end create_mat_impl



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

    def create_struct_printers(self):
        for struct_name, struct_def in self.structs.items():
            fOut = open( self.exec_dir + os.sep + "print_%s.cpp" % (struct_name), "w" )
            fOut.write( self.create_struct_printer( struct_name ) ) 
    # end create_struct_prnters

    def create_struct_generators(self):
        for struct_name, struct_def in self.structs.items():
            fOut = open( self.exec_dir + os.sep + "generate_%s.cpp" % (struct_name), "w" )
            fOut.write( self.create_struct_generator( struct_name ) ) 
    # end create_struct_generators

    def create_struct_headers(self):
        '''Creates all structure and matlab support headers'''
        for struct_name, struct_def in self.structs.items():
            fOut = open( self.inc_dir + os.sep + "%s_class_def.h" % (struct_name), "w" )
            fOut.write( self.create_struct_header( struct_name ) ) 
        for struct_name, struct_def in self.structs.items():
            fOut = open( self.mex_dir + os.sep + "%s_mat_support.h" % ( struct_name), "w" )
            fOut.write( self.create_mat_support_header( struct_name ) )
        fOut = open( self.out_dir + os.sep + "mainpage.h", "w" )
        fOut.write( self.create_doxygen_mainpage() )
    # end create_struct_headers

    def create_mat_files( self ):
        for struct_name, struct_def in self.structs.items():
            mat_files = self.create_mat_support( struct_name )
            for filename, inst in mat_files.items():
                fOut = open( self.mat_dir + os.sep + filename, "w" )
                fOut.write( inst )
                fOut.close()
    # end create_mat_files

    def create_struct_impls(self):
        '''Creates all structure and matlab support cpp files'''

        python_dir = os.path.dirname(os.path.realpath(__file__))
        c_files_res_dir  = python_dir + os.sep + '..' + os.sep + 'c_files'

        fOut = open( self.out_dir + os.sep + "CMakeLists.txt", "w" )
        fOut.write( self.create_cmake_lists() )
        fOut.close()

        for struct_name, struct_def in self.structs.items():
            # write the class def twice - one to a general c area, one to a matlab
            # support area, where it will be compiled with -fPIC
            class_def = self.create_struct_impl( struct_name ) 
            fOut = open( self.src_dir + os.sep + "%s_class_def.cpp" % ( struct_name), "w" )
            fOut.write( class_def )
            fOut = open( self.mex_dir + os.sep + "%s_class_def.cpp" % ( struct_name), "w" )
            fOut.write( class_def )
        for struct_name, struct_def in self.structs.items():
            fOut = open( self.mex_dir + os.sep + "%s_mat_support.cpp" % ( struct_name), "w" )
            fOut.write( self.create_mat_support_impl( struct_name ) )
        for struct_name, struct_def in self.structs.items():
            fOut = open( self.mex_dir + os.sep + "%s_mex_impl.cpp" % ( struct_name), "w" )
            fOut.write( self.create_mex_impl( struct_name ) )
        for struct_name, struct_def in self.structs.items():
            fOut = open( self.mat_dir + os.sep + "%s_mex_test.m" % ( struct_name ), "w" )
            fOut.write( self.create_mex_test( struct_name ) )
    # end create_struct_impl

    def create_directory_structure( self ):
        '''Creates all the required sub directories'''
        if not os.path.exists( self.out_dir ):
            os.mkdir( self.out_dir )
        self.mex_dir = self.out_dir + os.sep + 'mex/'
        self.inc_dir = self.out_dir + os.sep + 'inc/'
        self.src_dir = self.out_dir + os.sep + 'src/'
        self.exec_dir = self.out_dir + os.sep + 'exec/'
        self.cmake_dir = self.out_dir + os.sep + 'cmake_local_modules'
        self.mat_dir = self.out_dir + os.sep + 'mat/'
        self.py_dir  = self.out_dir + os.sep + 'python/'
        for d in self.mex_dir, self.inc_dir, self.src_dir, self.exec_dir, self.cmake_dir, self.mat_dir, self.py_dir:
            if not os.path.exists( d ):
                os.mkdir(d)

        # ----------- path of script file
        python_dir = os.path.dirname(os.path.realpath(__file__))
        cmake_res_dir  = python_dir + '/../cmake_files'
        shutil.copy( cmake_res_dir + '/Findoctave.cmake', self.cmake_dir + '/Findoctave.cmake' )
        shutil.copy( cmake_res_dir + '/Findmatlab.cmake', self.cmake_dir + '/Findmatlab.cmake' )
    # end create_directory_structure

def generate_mex( out_dir, basetypes, structs, project ):
    pass



if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface MEX Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'output_directory' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    # Preprocess and fill in missing fields
    A = AutoGenerator( args.json_basetypes_file, 
                       args.json_structures_file,
                       pad=args.pad )

    generate_mex( args.output_directory, 
                  A.basetypes,
                  A.structs,
                  A.project )
