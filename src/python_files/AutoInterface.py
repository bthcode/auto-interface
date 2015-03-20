##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil




T="    "
USAGE="""
USAGE: AutoGenerator.py <basetypes json file> <class definition json file> <output directory>
"""

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

    disp( 'writing {0}.props...' );
    {0}_mex_impl( 2, ref2, '{0}.props', 'out.' );

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
        name, impl = self.create_mat_write_props( struct_name )
        ret[ name ] = impl
        name, impl = self.create_mat_read_props( struct_name )
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

    def create_mat_write_props( self, struct_name ):
        ret = ''' function [] = write_props_{0}( fname, prefix, {0}_struct )
    
    % create c instance
    ref = {0}_mex_impl(0);

    % copy mat to c
    {0}_mex_impl( 9, ref, {0}_struct  );

    % write props
    {0}_mex_impl( 2, ref, fname, prefix );

    % delete the c structure
    {0}_mex_impl(1, ref );
end
'''.format( struct_name )
    
        return 'write_props_{0}.m'.format( struct_name ), ret
    # end create_mat_write_props

    def create_mat_read_props( self, struct_name ):
        ret = ''' function [ {0}_struct ] = read_props_{0}( fname, prefix )
    
    % create c instance
    ref = {0}_mex_impl(0);

    % set defaults
    {0}_mex_impl( 6, ref );

    % read props
    {0}_mex_impl( 3, ref, fname, prefix );

    % copy to matlab
    {0}_struct = {0}_mex_impl( 8, ref );

    % delete the c structure
    {0}_mex_impl(1, ref );
end
'''.format( struct_name )
    
        return 'read_props_{0}.m'.format( struct_name ), ret
    # end create_mat_read_props


##################################################################################
#
# Doxygen
#
##################################################################################


    def create_doxygen_mainpage(self):
        table = '<table><tr><th>Structure</th><th>Description</th></tr>\n'
        for struct_name, struct_def in self.structs.items():
            doc = ''
            ns = ''
            if struct_def.has_key( "NAMESPACE" ):
                ns = struct_def["NAMESPACE"]
            if struct_def.has_key( "DESCRIPTION" ):
                doc = struct_def['DESCRIPTION']
            table = table + T + '<tr><td>%s::%s</td><td>%s</td></tr>\n'  % ( ns, struct_name, doc )
        table = table + '</table>'
        ret = '''
/**
\\mainpage
\\section INTRO Introduction
\\section HOWTO HOWTO
\\section GeneratedClasses Generated Classes
%s
\\section GeneratedMatlab Generated Matlab
\\section Example
\\code 
foo
bar
\\endcode
*//
        ''' % ( table )
        return ret
    # end create_doxygen_mainpage
                


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
    case 2:
        write_props_{0}( nlhs, plhs, nrhs, prhs );
        break;
    case 3:
        read_props_{0}( nlhs, plhs, nrhs, prhs );
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
    case 7:
        validate_{0}( nlhs, plhs, nrhs, prhs );
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
void write_props_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

/**
 *  @brief Copy data stored in p to new\'d mxArray
 */ 
void read_props_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

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
void validate_{0}( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);

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
        ret =       '#include "%s_mat_support.h"\n' % (struct_name)
        ret = ret + '#include "%s_class_def.h"\n' % ( struct_name )
        ret = ret + '#include <fstream>\n'
        ret = ret + '#include <string>\n'
        ret = ret + '#include <string.h> // memcpy\n'
        ret = ret + '#include <mex.h>\n\n'

        struct_def = self.structs[ struct_name ]

        if struct_def.has_key( "NAMESPACE" ):
            ret = ret + 'using %s::%s;\n\n' % ( struct_def['NAMESPACE'], struct_name )


        ### 
        # Main driver function for going from c to matlab
        #
        ret = ret + 'mxArray * %s_to_mat( %s * p_%s )\n{\n'  % ( struct_name, struct_name, struct_name )
        ret = ret + T + '// Allocate a single mx struct to hold the data\n'
        ret = ret + T + 'mxArray * p_ret = alloc_mx_array_for_%s( 1 );\n\n' % ( struct_name )
        ret = ret + T + '// Copy data into that mxArray\n'
        ret = ret + T + '%s_to_mx_struct( p_%s, p_ret, 0 );\n' % ( struct_name, struct_name )
        ret = ret + T + 'return p_ret;\n'
        ret = ret + '}\n\n'


        ### 
        # Allocate an mx array for this data type with n_elements
        #
        ret = ret + 'mxArray * alloc_mx_array_for_%s( std::size_t n_elems )\n{\n' % ( struct_name )
        # 1. allocate the big mxArray
        ret = ret + T + 'const char * fields[] = { \n'
        for f in struct_def['FIELDS'][:-1]:
            ret = ret + T + T + '"%s",\n' % ( f['NAME'] )
        # handle the last element differently to close the c array properly...
        ret = ret  + T + T  +'"%s" };\n\n' % ( struct_def['FIELDS'][-1]['NAME'] )
        ret = ret + T + 'int ndim = 2;\n'
        ret = ret + T + 'mwSize dims[2] = {1,n_elems};\n'
        ret = ret + T + 'int number_of_fields = %s;\n' % ( len( struct_def['FIELDS'] ) )
        ret = ret + T + 'mexPrintf("calling create struct array\\n");\n'
        ret = ret + T + 'mxArray * p_ret = mxCreateStructArray( ndim, dims,\n'
        ret = ret + '                                         number_of_fields, fields );\n'
        ret = ret + T + 'return p_ret;\n'
        ret = ret + '}\n\n'


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
            elif f['TYPE'] == "COMPLEX" :
                c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
                # 1. Create numeric array
                ret = ret + T + '{\n'
                ret = ret + T + T + 'mxArray * p_tmp;\n'
                ret = ret + T + T + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                ret = ret + T + T + '\n'
                ret = ret + T + T + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxCOMPLEX);\n' % ( mat_type )
                # 2. Get pointer
                ret = ret + T + T + '%s * p_real = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                ret = ret + T + T + '%s * p_imag = ( %s * ) mxGetPi( p_tmp );\n' % ( c_type, c_type )
                # 3. Copy c data to that pointer
                ret = ret + T + T + 'p_real[0] = p_%s->%s.real();\n' % ( struct_name, f['NAME'] )
                ret = ret + T + T + 'p_imag[0] = p_%s->%s.real();\n' % ( struct_name, f['NAME'] )
                # 4. Set the mat struct element's point to the numeric array
                ret = ret + T + T + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
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

                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
                    # 1. Create numeric array
                    ret = ret + T + 'if ( p_%s->%s.size() ) {\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + 'mxArray * p_tmp;\n'
                    ret = ret + T + T + 'mwSize tmp_dims[2] = { p_%s->%s.size(), 1 };\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + '\n'
                    ret = ret + T + T + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxCOMPLEX);\n' % ( mat_type )
                    # 2. Get pointer
                    ret = ret + T + T + '%s * real_ptr = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                    ret = ret + T + T + '%s * imag_ptr = ( %s * ) mxGetPi( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointer
                    ret = ret + T + T + 'for ( std::size_t ii=0; ii < p_%s->%s.size(); ii++ ) {\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + T + 'real_ptr[ii] = p_%s->%s[ii].real();\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + T + 'imag_ptr[ii] = p_%s->%s[ii].imag();\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + '}\n'
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + T + T + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + T + '}\n'
                    ret = ret + T + 'else'
                    ret = ret + T + '{ // placeholder for empty vector\n'
                    ret = ret + T + T + 'mexPrintf( "empty vector for %s\\n" );\n' % f['NAME']
                    ret = ret + T + T + 'mxArray * p_tmp;\n'
                    ret = ret + T + T + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                    ret = ret + T + T + '\n'
                    ret = ret + T + T + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxCOMPLEX);\n' % ( mat_type )
                    # 2. Get pointer
                    ret = ret + T + T + '%s * real_ptr = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                    ret = ret + T + T + '%s * imag_ptr = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointero       
                    ret = ret + T + T + 'real_ptr[0] = 0;\n'
                    ret = ret + T + T + 'imag_ptr[0] = 0;\n'
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
                ret = ret + T + T + T + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                ret = ret + T + T + T + 'memcpy( &(p_%s->%s), ptr, sizeof( %s ) );\n' % ( struct_name, f['NAME'], c_type )
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
            elif f['TYPE'] == "COMPLEX":
                c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
                # 1. Get a pointer to the right place in the mxArray
                ret = ret + T + '{\n'
                ret = ret + T + T + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                ret = ret + T + T + 'if ( p_tmp )\n'
                ret = ret + T + T + '{\n'
                ret = ret + T + T + T + '%s * p_tmp1 = mxGetPr( p_tmp );\n' % ( c_type )
                ret = ret + T + T + T + '%s * p_tmp2 = mxGetPi( p_tmp );\n' % ( c_type )
                ret = ret + T + T + T + 'if ( p_tmp1 ) p_%s->%s.real( *p_tmp1 );\n' % ( struct_name, f['NAME'] )
                ret = ret + T + T + T + 'if ( p_tmp2 ) p_%s->%s.imag( *p_tmp2 );\n' % ( struct_name, f['NAME'] )
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
                elif f['CONTAINED_TYPE'] == "COMPLEX" :
                    c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
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
                    ret = ret + T + T + T + '%s * real_ptr = mxGetPr( p_tmp );\n' % ( c_type )
                    ret = ret + T + T + T + '%s * imag_ptr = mxGetPi( p_tmp );\n' % ( c_type )
                    ret = ret + T + T + T + '// Copy the data into c\n'
                    ret = ret + T + T + T + 'for (size_t i=0; i < num_elements; i++ )\n'
                    ret = ret + T + T + T + '{\n'
                    ret = ret + T + T + T + T + 'if ( real_ptr ) p_%s->%s[ i ].real( real_ptr[ i ] );\n' % ( struct_name, f['NAME'] )
                    ret = ret + T + T + T + T + 'if ( imag_ptr ) p_%s->%s[ i ].imag( imag_ptr[ i ] );\n' % ( struct_name, f['NAME'] )
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

        ### Write Props
        ret = ret + 'void write_props_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + T + '// call a %s object\'s write_props\n\n' % ( struct_name)
        ret = ret + T + 'char * file_name;\n'
        ret = ret + T + 'char * prefix;\n'
        ret = ret + T + 'int  buflen;\n'
        ret = ret + T + 'if ( nrhs != 4 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n\n'
        ret = ret + T + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n\n'
        ret = ret + T + 'if (mxIsChar(prhs[3]) != 1)\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + 'mexErrMsgTxt("Prefix must be a string.");'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n\n'
        ret = ret + T + '// copy file name and prefix into c strings\n'
        ret = ret + T + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + T + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + T + 'mxGetString(prhs[2], file_name, buflen);\n\n'
        ret = ret + T + 'buflen = (mxGetM(prhs[3]) * mxGetN(prhs[3])) + 1;\n'
        ret = ret + T + 'prefix = (char *)mxCalloc(buflen, sizeof(char));\n'
        ret = ret + T + 'mxGetString(prhs[3], prefix, buflen);\n\n'
        ret = ret + T + 'std::string pre( prefix );\n\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'std::ofstream f_out;\n'
        ret = ret + T + 'f_out.open( file_name );\n'
        ret = ret + T + 'p->write_props( f_out, pre );\n'
        ret = ret + '}\n\n'

        ### Read Props
        ret = ret + 'void read_props_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]) {\n' % ( struct_name )
        ret = ret + T + '// call a %s object\'s read_props\n' % ( struct_name )
        ret = ret + T + 'char * file_name;\n'
        ret = ret + T + 'char * prefix;\n'
        ret = ret + T + 'int  buflen;\n'
        ret = ret + T + 'if ( nrhs != 4 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + T + 'if (mxIsChar(prhs[3]) != 1)\n'
        ret = ret + T + T + '{\n'
        ret = ret + T + T + 'mexErrMsgTxt("Prefix must be a string.");'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + '// copy file name and prefix into c strings\n'
        ret = ret + T + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + T + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + T + 'mxGetString(prhs[2], file_name, buflen);\n'
        ret = ret + T + 'buflen = (mxGetM(prhs[3]) * mxGetN(prhs[3])) + 1;\n'
        ret = ret + T + 'prefix = (char *)mxCalloc(buflen, sizeof(char));\n'
        ret = ret + T + 'mxGetString(prhs[3], prefix, buflen);\n'
        ret = ret + T + 'std::string pre( prefix );\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'std::ifstream if_in;\n'
        ret = ret + T + 'if_in.open( file_name );\n'
        ret = ret + T + 'p->read_props( if_in, pre );\n'
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

        ### Validate
        ret = ret + 'void validate_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + T + '// call a %s object\'s validate\n' % ( struct_name )
        ret = ret + T + 'if ( nrhs != 2 )\n'
        ret = ret + T + '{\n'
        ret = ret + T + T + '// print error\n'
        ret = ret + T + T + 'return;\n'
        ret = ret + T + '}\n'
        ret = ret + T + '// cast to class pointer\n'
        ret = ret + T + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + T + 'std::string err_msg;\n'
        ret = ret + T + 'int err_count = p->validate( err_msg );\n'
        ret = ret + T + 'plhs[0] = mxCreateDoubleMatrix( 1, 1, mxREAL );\n'
        ret = ret + T + 'double * ptr = mxGetPr( plhs[0] );\n'
        ret = ret + T + '*ptr = double( err_count );\n' 
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
# C STRUCTURE DEFINITIONS AND IMPLEMENTATIONS
#
##################################################################################

    def create_struct_header( self, struct_name ):
        '''Creates the Primary Structure Header'''
        struct_def = self.structs[ struct_name ]

        ### HEADER Guards
        ret =       '#ifndef %s_H\n' % ( struct_name )
        ret = ret + '#define %s_H\n\n' % ( struct_name )

        ### Stock Includes
        ret = ret + '#include <stdlib.h>\n'
        ret = ret + '#include <cstddef>\n'
        ret = ret + '#include <stdint.h>\n'
        ret = ret + '#include <iostream>\n'
        ret = ret + '#include <string>\n'
        ret = ret + '#include <map>\n'
        ret = ret + '#include <complex>\n'
        ret = ret + '#include <vector>\n'
        ret = ret + '#include <fstream>\n'
        ret = ret + '#include <sstream>\n\n'
        ret = ret + '#include <props_parser.h>\n\n'

        ### Other generated deps
        deps = self.get_dependencies_for_struct( struct_name )
        for dep in deps:
            ret = ret + '#include "%s"' % dep + "\n"

        ### Namespace
        if struct_def.has_key( 'NAMESPACE'  ):
            ret = ret + '\nnamespace %s {\n\n' % ( struct_def[ 'NAMESPACE' ] )
    
        ret = ret + "\n/**\n * @brief %s\n */\n" % ( struct_def[ 'DESCRIPTION' ] )

        ### Class Def
        ret = ret + "class %s {\n\n" % ( struct_def[ 'NAME' ] )
        ret = ret + T + 'public :\n\n'
        ret = ret + T + T + '%s();\n\n' % ( struct_def[ 'NAME' ] )
        ret = ret + T + T + '~%s(){};' % ( struct_def[ 'NAME' ] )


        ### Member Data
        ret = ret + '\n\n    // Member Fields\n\n'
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                c_decl = self.basetypes[ f['TYPE'] ]['C_TYPE']
            elif f['TYPE'] == 'STRUCT':
                c_decl = '%s' % ( f['STRUCT_TYPE'] )
            elif f['TYPE'] == 'VECTOR':
                if f['CONTAINED_TYPE'] == 'STRUCT':
                    c_decl = 'std::vector< %s >' % ( f['STRUCT_TYPE'] )
                elif self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    c_decl = 'std::vector< %s >' % ( self.basetypes[ f['CONTAINED_TYPE'] ][ 'C_TYPE' ] )
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    c_decl = 'std::vector< std::complex< %s > >' % ( self.basetypes[ f['COMPLEX_TYPE' ] ][ 'C_TYPE' ] )
                else:
                    print 'ERROR - vector with unknown type or no CONTAINED_TYPE key'
                    sys.exit(1)
            elif f['TYPE'] == 'COMPLEX':
                c_decl = 'std::complex< %s >' % ( self.basetypes[ f['COMPLEX_TYPE' ] ][ 'C_TYPE' ] )
            else:
                print 'ERROR - vector with no TYPE'
                sys.exit(1)
            ret = ret + T + "%s  %s; ///<%s\n" % ( c_decl, f['NAME'], f['DESCRIPTION'] )

        ret = ret + T + 'std::size_t num_fields;\n'

        ### Member Functions
        ret = ret + "\n\n" + T + '// Member Functions\n\n'
        ret = ret + T + "void write_props( std::ostream& r_stream, std::string& r_prefix );\n\n"
        ret = ret + T + "int validate( std::string& err_msg );\n\n"
        ret = ret + T + "void set_defaults();\n\n"
        ret = ret + T + "void read_props( std::istream& r_in_stream, std::string& r_prefix );\n\n"
        ret = ret + T + "std::size_t read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix );\n\n"

        ## TODO: read/write to/from json

        ret = ret + T + "void write_binary( std::ofstream& r_out_stream );\n\n"
        ret = ret + T + "void read_binary( std::ifstream& r_in_stream );\n\n"

        ### End Class
        ret = ret + "};\n\n"

        ### End Namespace
        if struct_def.has_key( 'NAMESPACE' ):
            ret = ret + '} // namepsace\n\n'


        ret = ret + "#endif\n"
        return ret
    # end create_struct_headers

    def create_struct_generator( self, struct_name ):
        struct_def = self.structs[ struct_name ]

        ret = '#include "%s_class_def.h"\n\n' % ( struct_name )
        ret = ret + '#include <iostream>\n'
        ret = ret + '#include <fstream>\n'

        ### Namespace
        if struct_def.has_key( 'NAMESPACE'  ):
            ret = ret + '\n using %s::%s;\n' %( struct_def[ 'NAMESPACE' ], struct_name )

        ret = ret + 'int main( int argc, char* argv[] ) {\n'
        ret = ret + T + 'if (argc != 2) {\n'
        ret = ret + T + T + 'std::cout << "USAGE: print_%s < binfile >" << std::endl;\n' % struct_name
        ret = ret + T + T + 'exit(1);\n'
        ret = ret + T + '}\n'
        ## GENERATE DATA
        ret = ret + T + '%s tmp;\n' % ( struct_name )
        ret = ret + T + 'tmp.set_defaults();\n'
        ret = ret + T + 'std::ofstream out;\n'
        ret = ret + T + 'out.open( argv[1], std::ios::binary );\n' 
        ret = ret + T + 'tmp.write_binary(out);\n'
        ret = ret + T + 'out.close();\n'
        ret = ret + T + 'return 0;\n'
        ret = ret + '}\n'
        return ret
    # end create_struct printer


    def create_struct_printer( self, struct_name ):
        struct_def = self.structs[ struct_name ]

        ret = '#include "%s_class_def.h"\n\n' % ( struct_name )
        ret = ret + '#include <iostream>\n'
        ret = ret + '#include <fstream>\n'
        ret = ret + '#include <string>\n'

        ### Namespace
        if struct_def.has_key( 'NAMESPACE'  ):
            ret = ret + '\n using %s::%s;\n' %( struct_def[ 'NAMESPACE' ], struct_name )

        ret = ret + 'int main( int argc, char* argv[] ) {\n'
        ret = ret + T + 'if (argc != 2) {\n'
        ret = ret + T + T + 'std::cout << "USAGE: print_%s < binfile >" << std::endl;\n' % struct_name
        ret = ret + T + T + 'exit(1);\n'
        ret = ret + T + '}\n'
        ret = ret + T + '%s tmp;\n' % ( struct_name )
        ret = ret + T + 'std::ifstream in;\n'
        ret = ret + T + 'in.open( argv[1], std::ios::binary );\n'
        ret = ret + T + 'tmp.read_binary( in );\n'
        ret = ret + T + 'std::string prefix( "" );\n'
        ret = ret + T + 'tmp.write_props( std::cout, prefix );\n'
        ## READ IN DATA
        ret = ret + T + 'return 0;'
        ret = ret + '}\n'
        return ret
    # end create_struct printer
        


    def create_struct_impl( self, struct_name ):
        '''Creates the Primary Structure CPP Implementation'''

        struct_def = self.structs[ struct_name ]

        ret = '#include "%s_class_def.h"\n\n' % ( struct_name )

        ### Namespace
        if struct_def.has_key( 'NAMESPACE'  ):
            ret = ret + '\nnamespace %s {\n\n' % ( struct_def[ 'NAMESPACE' ] )

        ### Constructor
        ret = ret + '%s::%s() : num_fields(%s){}\n\n\n' % ( struct_name, struct_name, len( struct_def['FIELDS'] ) )

        ### Read Binary
        ret = ret + "void %s::read_binary( std::ifstream& r_stream ){\n\n" % ( struct_name )
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ) or f['TYPE'] == 'COMPLEX':
                ret = ret + T + 'r_stream.read( (char*)&(%s), sizeof(%s) );\n' %( f['NAME'], f['NAME'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + '%s.read_binary( r_stream );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                ret = ret + T + 'uint32_t tmp_%s_size;\n' % ( f['NAME'] )
                ret = ret + T + 'r_stream.read( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % ( f['NAME'], f['NAME'] )
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    ctype = self.basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                    ret = ret + T + 'for ( uint32_t ii=0; ii < tmp_%s_size; ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + T + T + '%s tmp_%s;\n' % ( ctype, ctype )
                    ret = ret + T + T + 'r_stream.read( (char*)&(tmp_%s), sizeof(tmp_%s));\n' % ( ctype, ctype )
                    ret = ret + T + T + '%s.push_back( tmp_%s );\n' % ( f['NAME'], ctype )
                    ret = ret + T + '}\n'
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ctype = f['STRUCT_TYPE']
                    ret = ret + T + 'for ( uint32_t ii=0; ii < tmp_%s_size; ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + T + T + '%s tmp_%s;\n' % ( ctype, ctype )
                    ret = ret + T + T + 'tmp_%s.read_binary( r_stream );\n' % ( ctype )
                    ret = ret + T + T + '%s.push_back( tmp_%s );\n' % ( f['NAME'], ctype )
                    ret = ret + T + '}\n'
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    ctype = 'std::complex< %s >' % self.basetypes[f['COMPLEX_TYPE']]['C_TYPE']
                    ret = ret + T + 'for ( uint32_t ii=0; ii < tmp_%s_size; ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + T + T + '%s tmp_cmplx;\n' % ( ctype )
                    ret = ret + T + T + 'r_stream.read( (char*)&(tmp_cmplx), sizeof(tmp_cmplx));\n' 
                    ret = ret + T + T + '%s.push_back( tmp_cmplx );\n' % ( f['NAME'] )
                    ret = ret + T + '}\n'
        ret = ret + "}\n\n"


        ### Write Binary
        ret = ret + "void %s::write_binary( std::ofstream& r_stream ){\n\n" % ( struct_name )
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ) or f['TYPE'] == 'COMPLEX':
                ret = ret + T + 'r_stream.write( (char*)&(%s), sizeof(%s) );\n' %( f['NAME'], f['NAME'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + '%s.write_binary( r_stream );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                ret = ret + T + 'uint32_t tmp_%s_size = %s.size();\n' % ( f['NAME'], f['NAME'] )
                ret = ret + T + 'r_stream.write( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % ( f['NAME'], f['NAME'] )
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ) or f['CONTAINED_TYPE'] == 'COMPLEX':
                    ret = ret + T + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + T + T + 'r_stream.write( (char*)&(%s[ii]), sizeof(%s[ii]));\n' % ( f['NAME'], f['NAME'] )
                    ret = ret + T + '}\n'
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + T + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + T + T + '%s[ii].write_binary( r_stream );\n' % ( f['NAME'] )
                    ret = ret + T + '}\n'
        ret = ret + "}\n\n"



        ### Write Props
        ret = ret + "void %s::write_props( std::ostream& r_stream, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + T + "std::string tmp;\n"
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if b.has_key('STREAM_CAST'):
                    c_print = T + 'r_stream << r_prefix << "%s = " << (%s)(%s) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'], f['NAME'] )
                else:
                    c_print = T + 'r_stream << r_prefix << "%s = " << %s << "\\n";\n' % ( f['NAME'], f['NAME'] )
                ret = ret + c_print
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + 'tmp = r_prefix + "%s.";\n' % ( f['NAME'] )
                c_print = T + '%s.write_props( r_stream, tmp );\n' % ( f['NAME'] )
                ret = ret + c_print
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    b = self.basetypes[ f['CONTAINED_TYPE'] ]
                    iter_decl  = T + T + 'std::vector< %s >::iterator ii;\n' % ( b['C_TYPE'] )
                    if b.has_key( 'STREAM_CAST' ):
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << %s((*ii)) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'] )
                    else:
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << (*ii) << "\\n";\n' % ( f['NAME'] )
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    b = self.basetypes[ f['COMPLEX_TYPE'] ]
                    iter_decl  = T + T + 'std::vector< std::complex< %s > >::iterator ii;\n' % ( b['C_TYPE'] )
                    if b.has_key( 'STREAM_CAST' ):
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << %s((*ii)) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'] )
                    else:
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << (*ii) << "\\n";\n' % ( f['NAME'] )
                
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    iter_decl = T + T + 'std::vector< %s >::iterator ii;\n' % ( f['STRUCT_TYPE'] )
                    print_decl = T + T + T + 'std::stringstream ss;\n'
                    print_decl = print_decl + T + T + T + 'ss << r_prefix << "%s[ " << count << " ].";\n' % ( f['NAME'] )
                    print_decl = print_decl + T + T + T + 'std::string tmp( ss.str() );\n'
                    print_decl = print_decl + T + T + T + 'ii->write_props( r_stream, tmp );\n'
                
                ret = ret + T + '{\n'
                ret = ret + iter_decl
                ret = ret + T + T +  'std::size_t count = 0;\n'
                ret = ret + T + T +  'for ( ii = %s.begin(); ii != %s.end(); ii++ )\n' %( f['NAME'], f['NAME'] )
                ret = ret + T + T +  '{\n'
                ret = ret + print_decl
                ret = ret + T + T +T +   'count++;\n'
                ret = ret + T + T +  '}\n'
                ret = ret + T + '}\n'
        ret = ret + "}\n\n"

        ### Read Props From Params
        ret = ret + "std::size_t %s::read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + T + 'std::string key;\n'
        ret = ret + T + 'std::map< std::string, std::string >::iterator param_iter;\n'
        ret = ret + T + 'std::size_t fields_found=0;\n'

        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                ret = ret + T + 'key = r_prefix + "%s";\n\n' % ( f['NAME'] )
                ret = ret + T + 'param_iter = r_params.find( key );\n'
                ret = ret + T + 'if ( param_iter != r_params.end() )\n'
                ret = ret + T + '{\n'
                ret = ret + T +T +  'std::stringstream ss( param_iter->second );\n'
                if b.has_key('STREAM_CAST'):
                    ret = ret + T +T +  '%s u;\n' % ( b[ 'STREAM_CAST' ] )
                    ret = ret + T +T +  'ss >> u;\n'
                    ret = ret + T +T +  '%s = (%s)( u );\n' % ( f['NAME'], b['STREAM_CAST' ] )
                else:
                    ret = ret + T +T +  'ss >> %s;\n' % ( f['NAME'] )
                ret = ret + T +T +  'fields_found++;\n'
                ret = ret + T + '}\n'
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + 'key = r_prefix + "%s.";\n' % ( f['NAME'] )
                ret = ret + T + 'fields_found += %s.read_props( r_params, key );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    # 1. Get the prefix
                    # 2. Go into a while loop incrementing count until no more keys 
                    #       are found
                    b = self.basetypes[ f['CONTAINED_TYPE'] ]
                    ret = ret + T + '{\n'
                    ret = ret + T + 'std::size_t count=0;\n'
                    ret = ret + T + 'while( 1 )\n'
                    ret = ret + T + '{\n'
                    ret = ret + T +T + 'std::stringstream ss;\n'
                    ret = ret + T +T + 'ss << r_prefix << "%s" << "[ " << count << " ]";\n' % ( f['NAME'] )
                    ret = ret + T +T + 'param_iter = r_params.find( ss.str() );\n' 
                    ret = ret + T +T + 'if ( param_iter == r_params.end() )\n'
                    ret = ret + T +T + T + 'break;\n'
                    ret = ret + T +T + 'else {\n'
                    ret = ret + T +T + T + 'std::stringstream ss2( param_iter->second );\n'
                    if b.has_key( 'STREAM_CAST' ):
                        ret = ret + T +T +T + '%s u;\n' % ( b[ 'STREAM_CAST' ] )
                        ret = ret + T +T +T + 'ss2 >> u;\n'
                        ret = ret + T +T +T + '%s.push_back(%s( u ));\n' % ( f['NAME'], b['STREAM_CAST' ] )
                    else:
                        ret = ret + T +T +T + '%s u;\n' % ( b[ 'C_TYPE' ] )
                        ret = ret + T +T +T + 'ss2 >> u;\n'
                        ret = ret + T +T +T + '%s.push_back(u);\n' % ( f['NAME'] ) 
                    ret = ret + T +T +T + 'count++;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T +T + 'fields_found += count;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T + '}\n'
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    # 1. Get the prefix
                    # 2. Go into a while loop incrementing count until no more keys 
                    #       are found
                    b = self.basetypes[ f['COMPLEX_TYPE'] ]
                    ret = ret + T + '{\n'
                    ret = ret + T + 'std::size_t count=0;\n'
                    ret = ret + T + 'while( 1 )\n'
                    ret = ret + T + '{\n'
                    ret = ret + T +T + 'std::stringstream ss;\n'
                    ret = ret + T +T + 'ss << r_prefix << "%s" << "[ " << count << " ]";\n' % ( f['NAME'] )
                    ret = ret + T +T + 'param_iter = r_params.find( ss.str() );\n' 
                    ret = ret + T +T + 'if ( param_iter == r_params.end() )\n'
                    ret = ret + T +T + T + 'break;\n'
                    ret = ret + T +T + 'else {\n'
                    ret = ret + T +T + T + 'std::stringstream ss2( param_iter->second );\n'
                    ret = ret + T +T +T + 'std::complex< %s > u;\n' % ( b[ 'C_TYPE' ] )
                    ret = ret + T +T +T + 'ss2 >> u;\n'
                    ret = ret + T +T +T + '%s.push_back(u);\n' % ( f['NAME'] ) 
                    ret = ret + T +T +T + 'count++;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T +T + 'fields_found += count;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T + '}\n'

                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + T + '{\n'
                    ret = ret + T + 'std::size_t count=0;\n'
                    ret = ret + T + 'while( 1 )\n'
                    ret = ret + T + '{\n'
                    ret = ret + T + T + 'std::stringstream ss;\n'
                    ret = ret + T + T + 'ss << r_prefix << "%s" << "[ " << count << " ].";\n' % ( f['NAME'] )
                    ret = ret + T + T + '%s tmp_%s;\n' % ( f[ 'STRUCT_TYPE' ], f['STRUCT_TYPE' ] )
                    ret = ret + T + T + 'tmp_%s.set_defaults();\n' % ( f['STRUCT_TYPE'] )
                    ret = ret + T + T + 'std::string s ( ss.str() );\n'
                    ret = ret + T + T + 'if ( tmp_%s.read_props( r_params, s )) {\n' % ( f['STRUCT_TYPE'] )
                    ret = ret + T + T + T + '%s.push_back( tmp_%s );\n' % ( f['NAME'], f['STRUCT_TYPE' ] )
                    ret = ret + T + T + '}\n'
                    ret = ret + T + T +  'else { break; }\n'
                    ret = ret + T + T + T + 'count++;\n'
                    ret = ret + T + T + '}\n'
                    ret = ret + T + 'fields_found += count;\n'
                    ret = ret + T + '}\n'
                
        ret = ret + T + 'return fields_found;\n'
        ret = ret + "}\n\n"


        ### Read Props From Stream
        ret = ret + "void %s::read_props( std::istream& r_in_stream, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + T + 'std::map< std::string, std::string > params;\n\n'
        ret = ret + T + 'parse_param_stream( r_in_stream, params );\n\n' 
        ret = ret + T + 'std::string key;\n'
        ret = ret + T + 'read_props( params, r_prefix );\n' 
        ret = ret + "}\n\n"

        ### Defaults
        ret = ret + "void %s::set_defaults( ){\n\n" % ( struct_name )
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if f.has_key('DEFAULT_VALUE'):
                    ret = ret + T + "%s = %s;\n" % ( f['NAME'], f['DEFAULT_VALUE'] )
                else:
                    ret = ret + T + "%s = %s;\n" % ( f['NAME'], b['DEFAULT_VALUE'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + '%s.set_defaults( );\n' % ( f['NAME'] )
        ret = ret + "}\n\n"

        ### Validate 
        ret = ret + "int %s::validate( std::string& err_msg ){\n\n" % ( struct_name )
        ret = ret + T + "int num_errs=0;\n"
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if f.has_key('VALID_MIN'):
                    ret = ret + T + "if ( %s < %s ) {\n" % ( f['NAME'], f['VALID_MIN'] )
                    ret = ret + T + T + 'err_msg +=  "Failed field: %s is less than %s\\n";\n' % ( f['NAME'], f['VALID_MIN'])
                    ret = ret + T + T + 'num_errs++;\n'
                    ret = ret + T + '}\n'
                if f.has_key('VALID_MAX'):
                    ret = ret + T + "if ( %s > %s ) {\n" % ( f['NAME'], f['VALID_MAX'] )
                    ret = ret + T + T + 'err_msg +=  "Failed field: %s is greater than %s\\n";\n' % ( f['NAME'], f['VALID_MAX'])
                    ret = ret + T + T + 'num_errs++;\n'
                    ret = ret + T + '}\n'
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + 'num_errs += %s.validate( err_msg );\n' % ( f['NAME'] )
        ret = ret + T + 'return num_errs;\n';
        ret = ret + "}\n\n"

        ### End Namespace
        if struct_def.has_key( 'NAMESPACE' ):
            ret = ret + '} // namepsace\n\n'

        return ret
    # end create_struct_impl


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

        shutil.copy( c_files_res_dir + os.sep + 'props_parser.cpp', 
                     self.src_dir + os.sep + 'props_parser.cpp' )

        shutil.copy( c_files_res_dir + os.sep + 'props_parser.h', 
                     self.src_dir + os.sep + 'props_parser.h' )

        # TODO: why am I copying this twice?
        shutil.copy( c_files_res_dir + os.sep + 'props_parser.h', 
                     self.mex_dir + os.sep + 'props_parser.h' )

        shutil.copy( c_files_res_dir + os.sep + 'props_parser.cpp', 
                     self.mex_dir + os.sep + 'props_parser.cpp' )

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
        for d in self.mex_dir, self.inc_dir, self.src_dir, self.exec_dir, self.cmake_dir, self.mat_dir:
            if not os.path.exists( d ):
                os.mkdir(d)

        # ----------- path of script file
        python_dir = os.path.dirname(os.path.realpath(__file__))
        cmake_res_dir  = python_dir + '/../cmake_files'
        shutil.copy( cmake_res_dir + '/Findoctave.cmake', self.cmake_dir + '/Findoctave.cmake' )
        shutil.copy( cmake_res_dir + '/Findmatlab.cmake', self.cmake_dir + '/Findmatlab.cmake' )
    # end create_directory_structure



if __name__ == "__main__":
    # TODO: parse tools
    if len( sys.argv ) != 4:
        print USAGE
        sys.exit(1)
    json_basetypes = sys.argv[1]
    json_file = sys.argv[2]
    out_dir = sys.argv[3]
    A = AutoGenerator( json_basetypes, json_file, out_dir  )
    A.create_struct_headers()
    A.create_struct_impls()
    A.create_struct_printers()
    A.create_struct_generators()
    A.create_mat_files() 
