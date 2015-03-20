##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os


PROPS_PARSER_C="""
#include "props_parser.h"

void parse_param_stream( std::istream& r_in_stream, 
                         std::map< std::string, std::string>& r_params )
{
    std::string line;
    while ( std::getline( r_in_stream, line ) )
    {
        //std::cout << "line pre = |" << line << "|" <<  std::endl;

        // 1. find and strip from the first comment on
        std::size_t ii;
        ii = line.find( "#" );
        if ( ii != line.npos )
        {
            line.erase( ii );
        }

        // 2. rstrip
        ii = line.find_last_not_of( " \\t\\n\\r" );
        if ( ii != line.npos )
        {
            line.erase( ii+1 );
        }

        // 3. lstrip
        ii = line.find_first_not_of( " \\t\\n\\r" );
        if ( ii != line.npos )
        {
            line.erase( 0, ii );
        }

        // 3. anything left on the line?
        if ( 0 == line.size() )
        {
            continue;
        }

        //std::cout << "line post = |" << line << "|" <<  std::endl;

        // 4. Find the = 
        ii = line.find( "=" );
        if ( ii != line.npos )
        {       
            std::string key = line.substr( 0,ii );
            std::string val = line.substr( ii+1, line.npos );


            ii = key.find_last_not_of( " \\t\\n\\r" );
            //std::cout << "key pre = |" << key << "|" << std::endl;
            if ( ii != key.npos )
            {
                key.erase( ii+1 );
            }
            //std::cout << "key post = |" << key << "|" << std::endl;


            //std::cout << "val pre = |" << val << "|" << std::endl;
            ii = val.find_first_not_of( " \\t\\n\\r" );
            if ( ii != val.npos )
            {
                val.erase( 0, ii );
            }
            //std::cout << "val post = |" << val << "|" << std::endl;
            r_params.insert( std::make_pair( key, val ) );
        }
    }
}

"""

PROPS_PARSER_H="""
#ifndef PROPS_PARSER_H
#define PROPS_PARSER_H

#include <string>
#include <map>
#include <vector>
#include <sstream>
#include <iostream>

void parse_param_stream( std::istream& r_in_stream, 
                         std::map< std::string, std::string >& r_params );

#endif
"""

TAB="    "
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
        ret = "% Auto generated test of " + struct_name + " mex interface"
        ret = ret + "addpath(cd)\n\n" 
        ret = ret + "\n"
        ret = ret + "disp( 'initializing c structures')\n"
        ret = ret + "ref = %s_mex_impl(0)\n" % ( struct_name )
        ret = ret + "ref2 = %s_mex_impl(0)\n" % ( struct_name )
        ret = ret + "ref3 = %s_mex_impl(0)\n" % ( struct_name )
        ret = ret + "\n"
        ret = ret + "disp( 'setting defaults...' )\n"
        ret = ret + "%s_mex_impl(6, ref )\n" % ( struct_name )
        ret = ret + "\n"
        ret = ret + "disp( 'copying from c to mat...' );\n"
        ret = ret + "foo = %s_mex_impl( 8, ref );\n" % ( struct_name )
        ret = ret + "\n"
        ret = ret + "disp( 'copying from mat to new c pointer...' );\n"
        ret = ret + "%s_mex_impl( 9, ref2, foo  );\n" %( struct_name )
        ret = ret + "\n"
        ret = ret + "disp( 'writing barf.props...' );\n"
        ret = ret + "%s_mex_impl( 2, ref2, 'barf.props', 'out.' );\n" % ( struct_name )
        ret = ret + "\n"
        ret = ret + "disp( 'writing binary barf.bin...');\n"
        ret = ret + "%s_mex_impl( 4, ref2, 'barf.bin' );\n" % ( struct_name )
        ret = ret + "\n"
        ret = ret + "disp( 'reading binary barf.bin...');\n"
        ret = ret + "%s_mex_impl( 5, ref3, 'barf.bin' );\n" % ( struct_name )
        ret = ret + "bar = %s_mex_impl( 8, ref3 )\n" % ( struct_name )
        ret = ret + "\n"
        ret = ret + "disp( 'deleting c structures' )\n"
        ret = ret + "%s_mex_impl(1, ref )\n" % ( struct_name )
        ret = ret + "%s_mex_impl(1, ref2 )\n" % ( struct_name )
        ret = ret + "%s_mex_impl(1, ref3 )\n" % ( struct_name )
        ret = ret + "disp( 'success' )\n"
        return ret
    # end create_mat_test
 


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
            table = table + TAB + '<tr><td>%s::%s</td><td>%s</td></tr>\n'  % ( ns, struct_name, doc )
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
        ret =       '#include "%s_class_def.h"\n' % ( struct_name )
        ret = ret + '#include "%s_mat_support.h"\n' % ( struct_name )
        ret = ret + '#include <mex.h>\n\n'

        ret = ret + '\n\n//Now the big MEX function\n\n'
        ret = ret + 'void  mexFunction (int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])'
        ret = ret + '{\n'
        ret = ret + TAB + 'int op_type;\n'
        ret = ret + TAB + 'if ( nrhs < 1 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error here\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + 'op_type = * mxGetPr( prhs[0] );\n\n'
        ret = ret + TAB + 'switch( op_type ) {\n'
        ret = ret + TAB + 'case 0:\n'
        ret = ret + TAB + TAB + 'init_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 1:\n'
        ret = ret + TAB + TAB + 'destroy_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 2:\n'
        ret = ret + TAB + TAB + 'write_props_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 3:\n'
        ret = ret + TAB + TAB + 'read_props_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 4:\n'
        ret = ret + TAB + TAB + 'write_binary_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 5:\n'
        ret = ret + TAB + TAB + 'read_binary_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 6:\n'
        ret = ret + TAB + TAB + 'set_defaults_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 7:\n'
        ret = ret + TAB + TAB + 'validate_%s( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 8:\n'
        ret = ret + TAB + TAB + '%s_cpp_to_mat( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'case 9:\n'
        ret = ret + TAB + TAB + '%s_mat_to_cpp( nlhs, plhs, nrhs, prhs );\n' % ( struct_name )
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + 'default:\n'
        ret = ret + TAB + TAB + '// raise error and return\n'
        ret = ret + TAB + TAB + 'break;\n'
        ret = ret + TAB + '}\n'
        ret = ret + '}\n'

        return ret
    # end create_mex


##################################################################################
#
# MATLAB Support Code
#
##################################################################################


    def create_mat_support_header( self, struct_name ):
        '''Creates the MATLAB Support Header'''
        ret =       '#ifndef %s_MAT_SUPPORT_H\n' % ( struct_name )
        ret = ret + '#define %s_MAT_SUPPORT_H\n\n' % ( struct_name )
        ret = ret + '#include "%s_class_def.h"\n' % ( struct_name )
        ret = ret + '#include <mex.h>\n\n'

        for header in self.get_mat_dependencies_for_struct( struct_name ):
            ret = ret + '#include "%s"\n' % ( header )
        ret = ret + '\n'

        struct_def = self.structs[ struct_name ]

        if struct_def.has_key( "NAMESPACE" ):
            ret = ret + 'using %s::%s;\n\n' % ( struct_def['NAMESPACE'], struct_name )
        ### Define sub functions
        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'mxArray * %s_to_mat( %s * p_%s );\n' % ( struct_name, struct_name, struct_name )

        ret = ret + '/**\n * @brief Copy mxArray to %s pointer\n */ \n' % ( struct_name )
        ret = ret + 'void mat_to_%s( const mxArray * pMat, %s * p_%s, std::size_t nth_element );\n\n' % ( struct_name, struct_name, struct_name )

        ret = ret + '/**\n * @brief Get uint64_t matlab value from %s pointer\n */ \n' % ( struct_name )
        ret = ret + 'mxArray * %s_pointer_to_mxArray( %s *p );\n\n' % ( struct_name, struct_name )

        ret = ret + '/**\n * @brief get pointer to %s from uint64_t stored in an mxArray\n */ \n' % ( struct_name )
        ret = ret + '%s * %s_pointer_from_mxArray( const mxArray * );\n\n' % ( struct_name, struct_name )

        ret = ret + '/**\n * @brief new a %s and return a uint64_t handle to matlab\n */ \n' % ( struct_name )
        ret = ret + 'void init_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % ( struct_name )

        ret = ret + '/**\n * @brief Delete %s from pointer stored in matlab uint64_t\n */ \n' % ( struct_name )
        ret = ret + 'void destroy_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % ( struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void write_props_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % (struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void read_props_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % ( struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void write_binary_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % (struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void read_binary_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % (struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void set_defaults_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % ( struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void validate_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % (struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void %s_cpp_to_mat( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % (struct_name )

        ret = ret + '/**\n * @brief Copy data stored in p to new\'d mxArray\n */ \n'
        ret = ret + 'void %s_mat_to_cpp( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]);\n\n' % (struct_name )

        ret = ret + '/**\n * @brief Do the actual data copy\n */\n'
        ret = ret + 'void %s_to_mx_struct( %s * p_%s, mxArray * p_ret, std::size_t nth_element );\n\n' % ( struct_name, struct_name, struct_name )

        ret = ret + '/**\n * @brief Allocate an mxArray for this data type\n */ \n'
        ret = ret + 'mxArray * alloc_mx_array_for_%s( std::size_t n_elems );\n' % ( struct_name )

        ret = ret + '#endif'

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
        ret = ret + TAB + '// Allocate a single mx struct to hold the data\n'
        ret = ret + TAB + 'mxArray * p_ret = alloc_mx_array_for_%s( 1 );\n\n' % ( struct_name )
        ret = ret + TAB + '// Copy data into that mxArray\n'
        ret = ret + TAB + '%s_to_mx_struct( p_%s, p_ret, 0 );\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'return p_ret;\n'
        ret = ret + '}\n\n'


        ### 
        # Allocate an mx array for this data type with n_elements
        #
        ret = ret + 'mxArray * alloc_mx_array_for_%s( std::size_t n_elems )\n{\n' % ( struct_name )
        # 1. allocate the big mxArray
        ret = ret + TAB + 'const char * fields[] = { \n'
        for f in struct_def['FIELDS'][:-1]:
            ret = ret + TAB + TAB + '"%s",\n' % ( f['NAME'] )
        # handle the last element differently to close the c array properly...
        ret = ret  + TAB + TAB  +'"%s" };\n\n' % ( struct_def['FIELDS'][-1]['NAME'] )
        ret = ret + TAB + 'int ndim = 2;\n'
        ret = ret + TAB + 'mwSize dims[2] = {1,n_elems};\n'
        ret = ret + TAB + 'int number_of_fields = %s;\n' % ( len( struct_def['FIELDS'] ) )
        ret = ret + TAB + 'mexPrintf("calling create struct array\\n");\n'
        ret = ret + TAB + 'mxArray * p_ret = mxCreateStructArray( ndim, dims,\n'
        ret = ret + '                                         number_of_fields, fields );\n'
        ret = ret + TAB + 'return p_ret;\n'
        ret = ret + '}\n\n'


        ### 
        # Do the actual data copy
        #
        ret = ret + 'void %s_to_mx_struct( %s * p_%s, mxArray * p_ret, std::size_t nth_element )\n' % ( struct_name, struct_name, struct_name )
        ret = ret + '{\n'
        count = 0
        for f in struct_def['FIELDS']:
            ret = ret + TAB + '// ---- %s -----\n' % ( f['NAME'] )
            if self.basetypes.has_key( f['TYPE'] ):
                c_type = self.basetypes[ f['TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['TYPE'] ]['MAT_TYPE']
                # 1. Create numeric array
                ret = ret + TAB + '{\n'
                ret = ret + TAB + TAB + 'mxArray * p_tmp;\n'
                ret = ret + TAB + TAB + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                ret = ret + TAB + TAB + '\n'
                ret = ret + TAB + TAB + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxREAL);\n' % ( mat_type )
                # 2. Get pointer
                ret = ret + TAB + TAB + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                # 3. Copy c data to that pointer
                ret = ret + TAB + TAB + 'memcpy( ptr, &(p_%s->%s), sizeof( %s ));\n' % ( struct_name, f['NAME'], c_type )
                # 4. Set the mat struct element's point to the numeric array
                ret = ret + TAB + TAB + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                ret = ret + TAB + '}\n\n'
            elif f['TYPE'] == "STRUCT":
                ret = ret + TAB + '{\n'
                ret = ret + TAB + TAB + 'mxArray * p_tmp = %s_to_mat( &(p_%s->%s) );\n' % ( f["STRUCT_TYPE"], struct_name, f['NAME'] )
                ret = ret + TAB + TAB + 'mxSetFieldByNumber( p_ret, nth_element, %s, p_tmp );\n' % ( count )
                ret = ret + TAB + '}\n\n'
            elif f['TYPE'] == "COMPLEX" :
                c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
                # 1. Create numeric array
                ret = ret + TAB + '{\n'
                ret = ret + TAB + TAB + 'mxArray * p_tmp;\n'
                ret = ret + TAB + TAB + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                ret = ret + TAB + TAB + '\n'
                ret = ret + TAB + TAB + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxCOMPLEX);\n' % ( mat_type )
                # 2. Get pointer
                ret = ret + TAB + TAB + '%s * p_real = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                ret = ret + TAB + TAB + '%s * p_imag = ( %s * ) mxGetPi( p_tmp );\n' % ( c_type, c_type )
                # 3. Copy c data to that pointer
                ret = ret + TAB + TAB + 'p_real[0] = p_%s->%s.real();\n' % ( struct_name, f['NAME'] )
                ret = ret + TAB + TAB + 'p_imag[0] = p_%s->%s.real();\n' % ( struct_name, f['NAME'] )
                # 4. Set the mat struct element's point to the numeric array
                ret = ret + TAB + TAB + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                ret = ret + TAB + '}\n\n'

            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    c_type = self.basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['CONTAINED_TYPE'] ]['MAT_TYPE']
                    # 1. Create numeric array
                    ret = ret + TAB + 'if ( p_%s->%s.size() ) {\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + 'mxArray * p_tmp;\n'
                    ret = ret + TAB + TAB + 'mwSize tmp_dims[2] = { p_%s->%s.size(), 1 };\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + '\n'
                    ret = ret + TAB + TAB + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxREAL);\n' % ( mat_type )
                    # 2. Get pointer
                    ret = ret + TAB + TAB + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointer
                    ret = ret + TAB + TAB + 'memcpy( ptr, (p_%s->%s.data()), sizeof( %s ) * p_%s->%s.size());\n' % ( struct_name, f['NAME'], c_type, struct_name, f['NAME'] )
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + TAB + TAB + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + TAB + '}\n'
                    ret = ret + TAB + 'else'
                    ret = ret + TAB + '{ // placeholder for empty vector\n'
                    ret = ret + TAB + TAB + 'mexPrintf( "empty vector for %s\\n" );\n' % f['NAME']
                    ret = ret + TAB + TAB + 'mxArray * p_tmp;\n'
                    ret = ret + TAB + TAB + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                    ret = ret + TAB + TAB + '\n'
                    ret = ret + TAB + TAB + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxREAL);\n' % ( mat_type )
                    ret = ret + TAB + TAB + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointero       
                    ret = ret + TAB + TAB + '%s t = 0;\n' % ( c_type )
                    ret = ret + TAB + TAB + 'memcpy( ptr, &(t), sizeof( %s ));\n' % ( c_type )
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + TAB + TAB + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + TAB + '}\n\n'

                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
                    # 1. Create numeric array
                    ret = ret + TAB + 'if ( p_%s->%s.size() ) {\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + 'mxArray * p_tmp;\n'
                    ret = ret + TAB + TAB + 'mwSize tmp_dims[2] = { p_%s->%s.size(), 1 };\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + '\n'
                    ret = ret + TAB + TAB + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxCOMPLEX);\n' % ( mat_type )
                    # 2. Get pointer
                    ret = ret + TAB + TAB + '%s * real_ptr = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                    ret = ret + TAB + TAB + '%s * imag_ptr = ( %s * ) mxGetPi( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointer
                    ret = ret + TAB + TAB + 'for ( std::size_t ii=0; ii < p_%s->%s.size(); ii++ ) {\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + 'real_ptr[ii] = p_%s->%s[ii].real();\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + 'imag_ptr[ii] = p_%s->%s[ii].imag();\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + '}\n'
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + TAB + TAB + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + TAB + '}\n'
                    ret = ret + TAB + 'else'
                    ret = ret + TAB + '{ // placeholder for empty vector\n'
                    ret = ret + TAB + TAB + 'mexPrintf( "empty vector for %s\\n" );\n' % f['NAME']
                    ret = ret + TAB + TAB + 'mxArray * p_tmp;\n'
                    ret = ret + TAB + TAB + 'mwSize tmp_dims[2] = { 1, 1 };\n'
                    ret = ret + TAB + TAB + '\n'
                    ret = ret + TAB + TAB + 'p_tmp = mxCreateNumericArray (2, tmp_dims, %s, mxCOMPLEX);\n' % ( mat_type )
                    # 2. Get pointer
                    ret = ret + TAB + TAB + '%s * real_ptr = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                    ret = ret + TAB + TAB + '%s * imag_ptr = ( %s * ) mxGetPr( p_tmp );\n' % ( c_type, c_type )
                    # 3. Copy c data to that pointero       
                    ret = ret + TAB + TAB + 'real_ptr[0] = 0;\n'
                    ret = ret + TAB + TAB + 'imag_ptr[0] = 0;\n'
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + TAB + TAB + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + TAB + '}\n\n'

     
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + TAB + 'if ( p_%s->%s.size() )\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + '{\n'

                    # 1. Create an mxArray of the correct length to hold the data:
                    ret = ret + TAB + TAB + 'mxArray * p_tmp = alloc_mx_array_for_%s( p_%s->%s.size() );\n' % ( f['STRUCT_TYPE'], struct_name, f['NAME'] )

                    # 2. Use the sub-structs mat_support file to generated an mxArray pointer
                    ret = ret + TAB + TAB + 'for ( size_t i=0; i < p_%s->%s.size(); i++ )\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + '{\n'

                    ret = ret + TAB + TAB + TAB + '%s_to_mx_struct( &(p_%s->%s[i]), p_tmp, i );\n' % ( f["STRUCT_TYPE"], struct_name, f['NAME'] )
                    # 4. Set the mat struct element's point to the numeric array
                    ret = ret + TAB + TAB + '}\n'

                    ret = ret + TAB + TAB + TAB + 'mxSetFieldByNumber (p_ret, nth_element, %s, p_tmp) ;\n' % ( count )
                    ret = ret + TAB + '}\n\n'
 
            else:
                ret = ret + TAB + 'mxSetFieldByNumber( p_ret, nth_element, %s, mxCreateString( "%s" ) );\n' % ( count, count )
            count = count + 1

        ret = ret + '}\n\n'

        ### 
        # Driver function to copy from mat to cpp
        #
        ret = ret + 'void mat_to_%s( const mxArray * pMat, %s * p_%s, std::size_t nth_element )\n{\n' % ( struct_name, struct_name, struct_name )
        ret = ret + TAB + '// Precondition: p_%s is assumed to be created elsewhere\n\n' % ( struct_name )
        count = 0
        for f in struct_def['FIELDS']:
            ret = ret + TAB + '// ------- %s -----------\n' % ( f['NAME'] )
            if self.basetypes.has_key( f['TYPE'] ):
                c_type = self.basetypes[ f['TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['TYPE'] ]['MAT_TYPE']
                # 1. Get a pointer to the right place in the mxArray
                ret = ret + TAB + '{\n'
                ret = ret + TAB + TAB + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                ret = ret + TAB + TAB + 'if ( p_tmp )\n'
                ret = ret + TAB + TAB + '{\n'
                ret = ret + TAB + TAB + TAB + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                ret = ret + TAB + TAB + TAB + 'memcpy( &(p_%s->%s), ptr, sizeof( %s ) );\n' % ( struct_name, f['NAME'], c_type )
                ret = ret + TAB + TAB + '}\n'
                ret = ret + TAB + '}\n\n'
            elif f['TYPE'] == "STRUCT":
                ret = ret + TAB + '{\n'
                ret = ret + TAB + TAB + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                ret = ret + TAB + TAB + 'if ( p_tmp )\n'
                ret = ret + TAB + TAB + '{\n'
                ret = ret + TAB + TAB + TAB + 'mat_to_%s( p_tmp, &(p_%s->%s), 0 );\n' % ( f['STRUCT_TYPE'], struct_name, f['NAME'] )
                ret = ret + TAB + TAB + '}\n'
                ret = ret + TAB + '}\n\n'
            elif f['TYPE'] == "COMPLEX":
                c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
                # 1. Get a pointer to the right place in the mxArray
                ret = ret + TAB + '{\n'
                ret = ret + TAB + TAB + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                ret = ret + TAB + TAB + 'if ( p_tmp )\n'
                ret = ret + TAB + TAB + '{\n'
                ret = ret + TAB + TAB + TAB + '%s * p_tmp1 = mxGetPr( p_tmp );\n' % ( c_type )
                ret = ret + TAB + TAB + TAB + '%s * p_tmp2 = mxGetPi( p_tmp );\n' % ( c_type )
                ret = ret + TAB + TAB + TAB + 'if ( p_tmp1 ) p_%s->%s.real( *p_tmp1 );\n' % ( struct_name, f['NAME'] )
                ret = ret + TAB + TAB + TAB + 'if ( p_tmp2 ) p_%s->%s.imag( *p_tmp2 );\n' % ( struct_name, f['NAME'] )
                ret = ret + TAB + TAB + '}\n'
                ret = ret + TAB + '}\n\n'
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    c_type = self.basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['CONTAINED_TYPE'] ]['MAT_TYPE']
                    ret = ret + TAB + '{\n'
                    # 1. Clear the output vector
                    ret = ret + TAB + 'p_%s->%s.clear();\n' % ( struct_name, f['NAME'] )
                    # 2. Get the new array size and resize the vector
                    ret = ret + TAB + TAB + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + 'if ( p_tmp )\n'
                    ret = ret + TAB + TAB + '{\n'
                    ret = ret + TAB + TAB + TAB + 'mwSize num_elements = mxGetNumberOfElements (p_tmp);\n'
                    ret = ret + TAB + TAB + TAB + 'p_%s->%s.resize( num_elements );\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + '// Get a raw pointer to the matlab storage\n'
                    ret = ret + TAB + TAB + TAB + '%s * ptr = ( %s * ) mxGetData( p_tmp );\n' % ( c_type, c_type )
                    ret = ret + TAB + TAB + TAB + '// Copy the data into c\n'
                    ret = ret + TAB + TAB + TAB + 'for (size_t i=0; i < num_elements; i++ )\n'
                    ret = ret + TAB + TAB + TAB + '{\n'
                    ret = ret + TAB + TAB + TAB + TAB + 'p_%s->%s[ i ] = (ptr[i]);\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + '}\n'
                    ret = ret + TAB + TAB + '}\n'
                    ret = ret + TAB + '}\n\n'
                elif f['CONTAINED_TYPE'] == "COMPLEX" :
                    c_type = self.basetypes[ f['COMPLEX_TYPE'] ]['C_TYPE']
                    mat_type = self.basetypes[ f['COMPLEX_TYPE'] ]['MAT_TYPE']
                    ret = ret + TAB + '{\n'
                    # 1. Clear the output vector
                    ret = ret + TAB + 'p_%s->%s.clear();\n' % ( struct_name, f['NAME'] )
                    # 2. Get the new array size and resize the vector
                    ret = ret + TAB + TAB + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + 'if ( p_tmp )\n'
                    ret = ret + TAB + TAB + '{\n'
                    ret = ret + TAB + TAB + TAB + 'mwSize num_elements = mxGetNumberOfElements (p_tmp);\n'
                    ret = ret + TAB + TAB + TAB + 'p_%s->%s.resize( num_elements );\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + '// Get a raw pointer to the matlab storage\n'
                    ret = ret + TAB + TAB + TAB + '%s * real_ptr = mxGetPr( p_tmp );\n' % ( c_type )
                    ret = ret + TAB + TAB + TAB + '%s * imag_ptr = mxGetPi( p_tmp );\n' % ( c_type )
                    ret = ret + TAB + TAB + TAB + '// Copy the data into c\n'
                    ret = ret + TAB + TAB + TAB + 'for (size_t i=0; i < num_elements; i++ )\n'
                    ret = ret + TAB + TAB + TAB + '{\n'
                    ret = ret + TAB + TAB + TAB + TAB + 'if ( real_ptr ) p_%s->%s[ i ].real( real_ptr[ i ] );\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + TAB + 'if ( imag_ptr ) p_%s->%s[ i ].imag( imag_ptr[ i ] );\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + '}\n'
                    ret = ret + TAB + TAB + '}\n'
                    ret = ret + TAB + '}\n\n'
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + TAB + '{\n'
                    # 1. Clear the output vector
                    ret = ret + TAB + 'p_%s->%s.clear();\n' % ( struct_name, f['NAME'] )
                    # 2. Get the new array size and resize the vector
                    ret = ret + TAB + TAB + 'mxArray * p_tmp = mxGetField (pMat, nth_element, "%s");\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + 'if ( p_tmp )\n'
                    ret = ret + TAB + TAB + '{\n'
                    ret = ret + TAB + TAB + TAB + 'mwSize num_elements = mxGetNumberOfElements (p_tmp);\n'
                    ret = ret + TAB + TAB + TAB + 'p_%s->%s.resize( num_elements );\n' % ( struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + '\n'
                    ret = ret + TAB + TAB + TAB + '// Copy the data into c\n'
                    ret = ret + TAB + TAB + TAB + 'for (size_t i=0; i < num_elements; i++ )\n'
                    ret = ret + TAB + TAB + TAB + '{\n'
                    ret = ret + TAB + TAB + TAB + TAB + 'mat_to_%s(p_tmp, &(p_%s->%s[i]), i);\n' % ( f['STRUCT_TYPE'], struct_name, f['NAME'] )
                    ret = ret + TAB + TAB + TAB + '}\n'
                    ret = ret + TAB + TAB + '}\n'
                    ret = ret + TAB + '}\n\n'
             
            count = count + 1
            # end for each field
 
        ret = ret + '}\n\n'

        ### Copy a pointer value into an mxArray
        ret = ret + 'mxArray * %s_pointer_to_mxArray( %s *p )\n{\n' % ( struct_name, struct_name )
        ret = ret + TAB + '// Allocate an mxArray to hold the data\n'
        ret = ret + TAB + 'mxArray * mxArr = mxCreateNumericMatrix( 1, 1, mxUINT64_CLASS, mxREAL );\n\n'
        ret = ret + TAB + '// Get a pointer to the mxArray\' data\n'
        ret = ret + TAB + 'uint64_t * ptr = (uint64_t*) mxGetData( mxArr );\n'
        ret = ret + TAB + '// Copy the pointer value\n\n'
        ret = ret + TAB + 'memcpy( ptr, &p, sizeof( %s * ));\n' % ( struct_name )
        ret = ret + TAB + 'return mxArr;\n'
        ret = ret + '}\n\n'

        ### Get a pointer value from an mxArray
        ret = ret + '%s * %s_pointer_from_mxArray( const mxArray * mxArray )\n{\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'uint64_t * ptr = ( uint64_t * ) mxGetData( mxArray );\n' 
        ret = ret + TAB + 'void * p_tmp[ 2 ];\n'
        ret = ret + TAB + 'memcpy( ( & ( p_tmp[ 0 ] ) ), ptr, sizeof( void * ) );\n'
        ret = ret + TAB + '%s * ret = ( %s * )( p_tmp[ 0 ] );\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'return ret;\n'
        ret = ret + '}\n\n'

        ### Init
        ret = ret + 'void init_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % ( struct_name )
        ret = ret + TAB + '// new a %s object, and send back a pointer\n' % ( struct_name )
        ret = ret + TAB + '%s * p = new %s;\n' % ( struct_name, struct_name );
        ret = ret + TAB + 'plhs[0] = %s_pointer_to_mxArray( p );\n' % ( struct_name ) 
        ret = ret + '}\n\n'

        ### Destroy
        ret = ret + 'void destroy_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % ( struct_name )
        ret = ret + TAB + '// destroy a %s object\n\n' % ( struct_name )
        ret = ret + TAB + 'if ( nrhs != 2 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'std::cout << "this is an error here..." << std::endl;\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'delete p;\n'
        ret = ret + '}\n\n'

        ### Write Props
        ret = ret + 'void write_props_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + TAB + '// call a %s object\'s write_props\n\n' % ( struct_name)
        ret = ret + TAB + 'char * file_name;\n'
        ret = ret + TAB + 'char * prefix;\n'
        ret = ret + TAB + 'int  buflen;\n'
        ret = ret + TAB + 'if ( nrhs != 4 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n\n'
        ret = ret + TAB + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n\n'
        ret = ret + TAB + 'if (mxIsChar(prhs[3]) != 1)\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + 'mexErrMsgTxt("Prefix must be a string.");'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n\n'
        ret = ret + TAB + '// copy file name and prefix into c strings\n'
        ret = ret + TAB + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + TAB + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + TAB + 'mxGetString(prhs[2], file_name, buflen);\n\n'
        ret = ret + TAB + 'buflen = (mxGetM(prhs[3]) * mxGetN(prhs[3])) + 1;\n'
        ret = ret + TAB + 'prefix = (char *)mxCalloc(buflen, sizeof(char));\n'
        ret = ret + TAB + 'mxGetString(prhs[3], prefix, buflen);\n\n'
        ret = ret + TAB + 'std::string pre( prefix );\n\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'std::ofstream f_out;\n'
        ret = ret + TAB + 'f_out.open( file_name );\n'
        ret = ret + TAB + 'p->write_props( f_out, pre );\n'
        ret = ret + '}\n\n'

        ### Read Props
        ret = ret + 'void read_props_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[]) {\n' % ( struct_name )
        ret = ret + TAB + '// call a %s object\'s read_props\n' % ( struct_name )
        ret = ret + TAB + 'char * file_name;\n'
        ret = ret + TAB + 'char * prefix;\n'
        ret = ret + TAB + 'int  buflen;\n'
        ret = ret + TAB + 'if ( nrhs != 4 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + TAB + 'if (mxIsChar(prhs[3]) != 1)\n'
        ret = ret + TAB + TAB + '{\n'
        ret = ret + TAB + TAB + 'mexErrMsgTxt("Prefix must be a string.");'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + '// copy file name and prefix into c strings\n'
        ret = ret + TAB + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + TAB + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + TAB + 'mxGetString(prhs[2], file_name, buflen);\n'
        ret = ret + TAB + 'buflen = (mxGetM(prhs[3]) * mxGetN(prhs[3])) + 1;\n'
        ret = ret + TAB + 'prefix = (char *)mxCalloc(buflen, sizeof(char));\n'
        ret = ret + TAB + 'mxGetString(prhs[3], prefix, buflen);\n'
        ret = ret + TAB + 'std::string pre( prefix );\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'std::ifstream if_in;\n'
        ret = ret + TAB + 'if_in.open( file_name );\n'
        ret = ret + TAB + 'p->read_props( if_in, pre );\n'
        ret = ret + '}\n\n'

        ### Write Binary
        ret = ret + 'void write_binary_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + TAB + '// call a %s object\'s write_binary\n' % ( struct_name )
        ret = ret + TAB + 'char * file_name;\n'
        ret = ret + TAB + 'int  buflen;\n'
        ret = ret + TAB + 'if ( nrhs != 3 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + '// copy file name and prefix into c strings\n'
        ret = ret + TAB + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + TAB + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + TAB + 'mxGetString(prhs[2], file_name, buflen);\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'std::ofstream of_out;\n'
        ret = ret + TAB + 'of_out.open( file_name, std::ios::binary );\n'
        ret = ret + TAB + 'p->write_binary( of_out );\n'

        ret = ret + '}\n\n'

        ### Read Binary
        ret = ret + 'void read_binary_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + TAB + '// call a %s object\'s read_binary\n' % ( struct_name )
        ret = ret + TAB + 'char * file_name;\n'
        ret = ret + TAB + 'int  buflen;\n'
        ret = ret + TAB + 'if ( nrhs != 3 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + 'if (mxIsChar(prhs[2]) != 1)\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + 'mexErrMsgTxt("Filename must be a string.");'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + '// copy file name and prefix into c strings\n'
        ret = ret + TAB + 'buflen = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;\n'
        ret = ret + TAB + 'file_name = (char * )mxCalloc(buflen, sizeof(char));\n'
        ret = ret + TAB + 'mxGetString(prhs[2], file_name, buflen);\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'std::ifstream if_in;\n'
        ret = ret + TAB + 'if_in.open( file_name, std::ios::binary );\n'
        ret = ret + TAB + 'p->read_binary( if_in );\n'
        ret = ret + '}\n\n'

        ### Set Defaults
        ret = ret + 'void set_defaults_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % ( struct_name )
        ret = ret + TAB + '// call a %s object\'s set_defaults\n' % ( struct_name )
        ret = ret + TAB + 'if ( nrhs != 2 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'p->set_defaults();\n'
        ret = ret + '}\n\n'

        ### Validate
        ret = ret + 'void validate_%s( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + TAB + '// call a %s object\'s validate\n' % ( struct_name )
        ret = ret + TAB + 'if ( nrhs != 2 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'std::string err_msg;\n'
        ret = ret + TAB + 'int err_count = p->validate( err_msg );\n'
        ret = ret + TAB + 'plhs[0] = mxCreateDoubleMatrix( 1, 1, mxREAL );\n'
        ret = ret + TAB + 'double * ptr = mxGetPr( plhs[0] );\n'
        ret = ret + TAB + '*ptr = double( err_count );\n' 
        ret = ret + '}\n\n'

        ### Cpp to Mat
        ret = ret + 'void %s_cpp_to_mat( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + TAB + '// copy %s object to matlab object\n' % ( struct_name )
        ret = ret + TAB + 'if ( nrhs != 2 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + '// print error\n'
        ret = ret + TAB + TAB + 'return;\n'
        ret = ret + TAB + '}\n'
        ret = ret + TAB + '// cast to class pointer\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + 'plhs[0] = %s_to_mat( p );\n' % ( struct_name )
        ret = ret + '}\n\n'

        ### Mat to Cpp
        ret = ret + 'void %s_mat_to_cpp( int nlhs, mxArray * plhs[], int nrhs, const mxArray * prhs[])\n{\n' % (struct_name )
        ret = ret + TAB + '// copy %s matlab object to cpp object\n' % ( struct_name )
        ret = ret + TAB + 'if ( nrhs != 3 )\n'
        ret = ret + TAB + '{\n'
        ret = ret + TAB + TAB + 'mexPrintf("Error, not enough arguments\\n");\n'
        ret = ret + TAB + TAB + 'return;'
        ret = ret + TAB + '}\n\n'
        ret = ret + TAB + '// Copy pointer from reference\n'
        ret = ret + TAB + '%s * p = %s_pointer_from_mxArray( prhs[1] );\n\n' % ( struct_name, struct_name )
        ret = ret + TAB + '// Make the call\n'
        ret = ret + TAB + 'mat_to_%s( prhs[2], p, 0 );\n' % ( struct_name )
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
        ret = ret + TAB + 'public :\n\n'
        ret = ret + TAB + TAB + '%s();\n\n' % ( struct_def[ 'NAME' ] )
        ret = ret + TAB + TAB + '~%s(){};' % ( struct_def[ 'NAME' ] )


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
            ret = ret + TAB + "%s  %s; ///<%s\n" % ( c_decl, f['NAME'], f['DESCRIPTION'] )

        ret = ret + TAB + 'std::size_t num_fields;\n'

        ### Member Functions
        ret = ret + "\n\n" + TAB + '// Member Functions\n\n'
        ret = ret + TAB + "void write_props( std::ostream& r_stream, std::string& r_prefix );\n\n"
        ret = ret + TAB + "int validate( std::string& err_msg );\n\n"
        ret = ret + TAB + "void set_defaults();\n\n"
        ret = ret + TAB + "void read_props( std::istream& r_in_stream, std::string& r_prefix );\n\n"
        ret = ret + TAB + "std::size_t read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix );\n\n"

        ## TODO: read/write to/from json

        ret = ret + TAB + "void write_binary( std::ofstream& r_out_stream );\n\n"
        ret = ret + TAB + "void read_binary( std::ifstream& r_in_stream );\n\n"

        ### End Class
        ret = ret + "};\n\n"

        ### End Namespace
        if struct_def.has_key( 'NAMESPACE' ):
            ret = ret + '} // namepsace\n\n'


        ret = ret + "#endif\n"
        return ret
    # end create_struct_headers





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
                ret = ret + TAB + 'r_stream.read( (char*)&(%s), sizeof(%s) );\n' %( f['NAME'], f['NAME'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + TAB + '%s.read_binary( r_stream );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                ret = ret + TAB + 'uint32_t tmp_%s_size;\n' % ( f['NAME'] )
                ret = ret + TAB + 'r_stream.read( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % ( f['NAME'], f['NAME'] )
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    ctype = self.basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                    ret = ret + TAB + 'for ( uint32_t ii=0; ii < tmp_%s_size; ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + '%s tmp_%s;\n' % ( ctype, ctype )
                    ret = ret + TAB + TAB + 'r_stream.read( (char*)&(tmp_%s), sizeof(tmp_%s));\n' % ( ctype, ctype )
                    ret = ret + TAB + TAB + '%s.push_back( tmp_%s );\n' % ( f['NAME'], ctype )
                    ret = ret + TAB + '}\n'
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ctype = f['STRUCT_TYPE']
                    ret = ret + TAB + 'for ( uint32_t ii=0; ii < tmp_%s_size; ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + '%s tmp_%s;\n' % ( ctype, ctype )
                    ret = ret + TAB + TAB + 'tmp_%s.read_binary( r_stream );\n' % ( ctype )
                    ret = ret + TAB + TAB + '%s.push_back( tmp_%s );\n' % ( f['NAME'], ctype )
                    ret = ret + TAB + '}\n'
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    ctype = 'std::complex< %s >' % self.basetypes[f['COMPLEX_TYPE']]['C_TYPE']
                    ret = ret + TAB + 'for ( uint32_t ii=0; ii < tmp_%s_size; ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + '%s tmp_cmplx;\n' % ( ctype )
                    ret = ret + TAB + TAB + 'r_stream.read( (char*)&(tmp_cmplx), sizeof(tmp_cmplx));\n' 
                    ret = ret + TAB + TAB + '%s.push_back( tmp_cmplx );\n' % ( f['NAME'] )
                    ret = ret + TAB + '}\n'
        ret = ret + "}\n\n"


        ### Write Binary
        ret = ret + "void %s::write_binary( std::ofstream& r_stream ){\n\n" % ( struct_name )
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ) or f['TYPE'] == 'COMPLEX':
                ret = ret + TAB + 'r_stream.write( (char*)&(%s), sizeof(%s) );\n' %( f['NAME'], f['NAME'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + TAB + '%s.write_binary( r_stream );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                ret = ret + TAB + 'uint32_t tmp_%s_size = %s.size();\n' % ( f['NAME'], f['NAME'] )
                ret = ret + TAB + 'r_stream.write( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % ( f['NAME'], f['NAME'] )
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ) or f['CONTAINED_TYPE'] == 'COMPLEX':
                    ret = ret + TAB + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + 'r_stream.write( (char*)&(%s[ii]), sizeof(%s[ii]));\n' % ( f['NAME'], f['NAME'] )
                    ret = ret + TAB + '}\n'
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + TAB + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + '%s[ii].write_binary( r_stream );\n' % ( f['NAME'] )
                    ret = ret + TAB + '}\n'
        ret = ret + "}\n\n"



        ### Write Props
        ret = ret + "void %s::write_props( std::ostream& r_stream, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + TAB + "std::string tmp;\n"
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if b.has_key('STREAM_CAST'):
                    c_print = TAB + 'r_stream << r_prefix << "%s = " << (%s)(%s) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'], f['NAME'] )
                else:
                    c_print = TAB + 'r_stream << r_prefix << "%s = " << %s << "\\n";\n' % ( f['NAME'], f['NAME'] )
                ret = ret + c_print
            elif f['TYPE'] == 'STRUCT':
                ret = ret + TAB + 'tmp = r_prefix + "%s.";\n' % ( f['NAME'] )
                c_print = TAB + '%s.write_props( r_stream, tmp );\n' % ( f['NAME'] )
                ret = ret + c_print
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    b = self.basetypes[ f['CONTAINED_TYPE'] ]
                    iter_decl  = TAB + TAB + 'std::vector< %s >::iterator ii;\n' % ( b['C_TYPE'] )
                    if b.has_key( 'STREAM_CAST' ):
                        print_decl = TAB + TAB + TAB + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << %s((*ii)) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'] )
                    else:
                        print_decl = TAB + TAB + TAB + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << (*ii) << "\\n";\n' % ( f['NAME'] )
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    b = self.basetypes[ f['COMPLEX_TYPE'] ]
                    iter_decl  = TAB + TAB + 'std::vector< std::complex< %s > >::iterator ii;\n' % ( b['C_TYPE'] )
                    if b.has_key( 'STREAM_CAST' ):
                        print_decl = TAB + TAB + TAB + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << %s((*ii)) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'] )
                    else:
                        print_decl = TAB + TAB + TAB + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << (*ii) << "\\n";\n' % ( f['NAME'] )
                
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    iter_decl = TAB + TAB + 'std::vector< %s >::iterator ii;\n' % ( f['STRUCT_TYPE'] )
                    print_decl = TAB + TAB + TAB + 'std::stringstream ss;\n'
                    print_decl = print_decl + TAB + TAB + TAB + 'ss << r_prefix << "%s[ " << count << " ].";\n' % ( f['NAME'] )
                    print_decl = print_decl + TAB + TAB + TAB + 'std::string tmp( ss.str() );\n'
                    print_decl = print_decl + TAB + TAB + TAB + 'ii->write_props( r_stream, tmp );\n'
                
                ret = ret + TAB + '{\n'
                ret = ret + iter_decl
                ret = ret + TAB + TAB +  'std::size_t count = 0;\n'
                ret = ret + TAB + TAB +  'for ( ii = %s.begin(); ii != %s.end(); ii++ )\n' %( f['NAME'], f['NAME'] )
                ret = ret + TAB + TAB +  '{\n'
                ret = ret + print_decl
                ret = ret + TAB + TAB +TAB +   'count++;\n'
                ret = ret + TAB + TAB +  '}\n'
                ret = ret + TAB + '}\n'
        ret = ret + "}\n\n"

        ### Read Props From Params
        ret = ret + "std::size_t %s::read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + TAB + 'std::string key;\n'
        ret = ret + TAB + 'std::map< std::string, std::string >::iterator param_iter;\n'
        ret = ret + TAB + 'std::size_t fields_found=0;\n'

        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                ret = ret + TAB + 'key = r_prefix + "%s";\n\n' % ( f['NAME'] )
                ret = ret + TAB + 'param_iter = r_params.find( key );\n'
                ret = ret + TAB + 'if ( param_iter != r_params.end() )\n'
                ret = ret + TAB + '{\n'
                ret = ret + TAB +TAB +  'std::stringstream ss( param_iter->second );\n'
                if b.has_key('STREAM_CAST'):
                    ret = ret + TAB +TAB +  '%s u;\n' % ( b[ 'STREAM_CAST' ] )
                    ret = ret + TAB +TAB +  'ss >> u;\n'
                    ret = ret + TAB +TAB +  '%s = (%s)( u );\n' % ( f['NAME'], b['STREAM_CAST' ] )
                else:
                    ret = ret + TAB +TAB +  'ss >> %s;\n' % ( f['NAME'] )
                ret = ret + TAB +TAB +  'fields_found++;\n'
                ret = ret + TAB + '}\n'
            elif f['TYPE'] == 'STRUCT':
                ret = ret + TAB + 'key = r_prefix + "%s.";\n' % ( f['NAME'] )
                ret = ret + TAB + 'fields_found += %s.read_props( r_params, key );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    # 1. Get the prefix
                    # 2. Go into a while loop incrementing count until no more keys 
                    #       are found
                    b = self.basetypes[ f['CONTAINED_TYPE'] ]
                    ret = ret + TAB + '{\n'
                    ret = ret + TAB + 'std::size_t count=0;\n'
                    ret = ret + TAB + 'while( 1 )\n'
                    ret = ret + TAB + '{\n'
                    ret = ret + TAB +TAB + 'std::stringstream ss;\n'
                    ret = ret + TAB +TAB + 'ss << r_prefix << "%s" << "[ " << count << " ]";\n' % ( f['NAME'] )
                    ret = ret + TAB +TAB + 'param_iter = r_params.find( ss.str() );\n' 
                    ret = ret + TAB +TAB + 'if ( param_iter == r_params.end() )\n'
                    ret = ret + TAB +TAB + TAB + 'break;\n'
                    ret = ret + TAB +TAB + 'else {\n'
                    ret = ret + TAB +TAB + TAB + 'std::stringstream ss2( param_iter->second );\n'
                    if b.has_key( 'STREAM_CAST' ):
                        ret = ret + TAB +TAB +TAB + '%s u;\n' % ( b[ 'STREAM_CAST' ] )
                        ret = ret + TAB +TAB +TAB + 'ss2 >> u;\n'
                        ret = ret + TAB +TAB +TAB + '%s.push_back(%s( u ));\n' % ( f['NAME'], b['STREAM_CAST' ] )
                    else:
                        ret = ret + TAB +TAB +TAB + '%s u;\n' % ( b[ 'C_TYPE' ] )
                        ret = ret + TAB +TAB +TAB + 'ss2 >> u;\n'
                        ret = ret + TAB +TAB +TAB + '%s.push_back(u);\n' % ( f['NAME'] ) 
                    ret = ret + TAB +TAB +TAB + 'count++;\n'
                    ret = ret + TAB +TAB + '}\n'
                    ret = ret + TAB +TAB + 'fields_found += count;\n'
                    ret = ret + TAB +TAB + '}\n'
                    ret = ret + TAB + '}\n'
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    # 1. Get the prefix
                    # 2. Go into a while loop incrementing count until no more keys 
                    #       are found
                    b = self.basetypes[ f['COMPLEX_TYPE'] ]
                    ret = ret + TAB + '{\n'
                    ret = ret + TAB + 'std::size_t count=0;\n'
                    ret = ret + TAB + 'while( 1 )\n'
                    ret = ret + TAB + '{\n'
                    ret = ret + TAB +TAB + 'std::stringstream ss;\n'
                    ret = ret + TAB +TAB + 'ss << r_prefix << "%s" << "[ " << count << " ]";\n' % ( f['NAME'] )
                    ret = ret + TAB +TAB + 'param_iter = r_params.find( ss.str() );\n' 
                    ret = ret + TAB +TAB + 'if ( param_iter == r_params.end() )\n'
                    ret = ret + TAB +TAB + TAB + 'break;\n'
                    ret = ret + TAB +TAB + 'else {\n'
                    ret = ret + TAB +TAB + TAB + 'std::stringstream ss2( param_iter->second );\n'
                    ret = ret + TAB +TAB +TAB + 'std::complex< %s > u;\n' % ( b[ 'C_TYPE' ] )
                    ret = ret + TAB +TAB +TAB + 'ss2 >> u;\n'
                    ret = ret + TAB +TAB +TAB + '%s.push_back(u);\n' % ( f['NAME'] ) 
                    ret = ret + TAB +TAB +TAB + 'count++;\n'
                    ret = ret + TAB +TAB + '}\n'
                    ret = ret + TAB +TAB + 'fields_found += count;\n'
                    ret = ret + TAB +TAB + '}\n'
                    ret = ret + TAB + '}\n'

                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + TAB + '{\n'
                    ret = ret + TAB + 'std::size_t count=0;\n'
                    ret = ret + TAB + 'while( 1 )\n'
                    ret = ret + TAB + '{\n'
                    ret = ret + TAB + TAB + 'std::stringstream ss;\n'
                    ret = ret + TAB + TAB + 'ss << r_prefix << "%s" << "[ " << count << " ].";\n' % ( f['NAME'] )
                    ret = ret + TAB + TAB + '%s tmp_%s;\n' % ( f[ 'STRUCT_TYPE' ], f['STRUCT_TYPE' ] )
                    ret = ret + TAB + TAB + 'tmp_%s.set_defaults();\n' % ( f['STRUCT_TYPE'] )
                    ret = ret + TAB + TAB + 'std::string s ( ss.str() );\n'
                    ret = ret + TAB + TAB + 'if ( tmp_%s.read_props( r_params, s )) {\n' % ( f['STRUCT_TYPE'] )
                    ret = ret + TAB + TAB + TAB + '%s.push_back( tmp_%s );\n' % ( f['NAME'], f['STRUCT_TYPE' ] )
                    ret = ret + TAB + TAB + '}\n'
                    ret = ret + TAB + TAB +  'else { break; }\n'
                    ret = ret + TAB + TAB + TAB + 'count++;\n'
                    ret = ret + TAB + TAB + '}\n'
                    ret = ret + TAB + 'fields_found += count;\n'
                    ret = ret + TAB + '}\n'
                
        ret = ret + TAB + 'return fields_found;\n'
        ret = ret + "}\n\n"


        ### Read Props From Stream
        ret = ret + "void %s::read_props( std::istream& r_in_stream, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + TAB + 'std::map< std::string, std::string > params;\n\n'
        ret = ret + TAB + 'parse_param_stream( r_in_stream, params );\n\n' 
        ret = ret + TAB + 'std::string key;\n'
        ret = ret + TAB + 'read_props( params, r_prefix );\n' 
        ret = ret + "}\n\n"

        ### Defaults
        ret = ret + "void %s::set_defaults( ){\n\n" % ( struct_name )
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if f.has_key('DEFAULT_VALUE'):
                    ret = ret + TAB + "%s = %s;\n" % ( f['NAME'], f['DEFAULT_VALUE'] )
                else:
                    ret = ret + TAB + "%s = %s;\n" % ( f['NAME'], b['DEFAULT_VALUE'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + TAB + '%s.set_defaults( );\n' % ( f['NAME'] )
        ret = ret + "}\n\n"

        ### Validate 
        ret = ret + "int %s::validate( std::string& err_msg ){\n\n" % ( struct_name )
        ret = ret + TAB + "int num_errs=0;\n"
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if f.has_key('VALID_MIN'):
                    ret = ret + TAB + "if ( %s < %s ) {\n" % ( f['NAME'], f['VALID_MIN'] )
                    ret = ret + TAB + TAB + 'err_msg +=  "Failed field: %s is less than %s\\n";\n' % ( f['NAME'], f['VALID_MIN'])
                    ret = ret + TAB + TAB + 'num_errs++;\n'
                    ret = ret + TAB + '}\n'
                if f.has_key('VALID_MAX'):
                    ret = ret + TAB + "if ( %s > %s ) {\n" % ( f['NAME'], f['VALID_MAX'] )
                    ret = ret + TAB + TAB + 'err_msg +=  "Failed field: %s is greater than %s\\n";\n' % ( f['NAME'], f['VALID_MAX'])
                    ret = ret + TAB + TAB + 'num_errs++;\n'
                    ret = ret + TAB + '}\n'
            elif f['TYPE'] == 'STRUCT':
                ret = ret + TAB + 'num_errs += %s.validate( err_msg );\n' % ( f['NAME'] )
        ret = ret + TAB + 'return num_errs;\n';
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

SET( CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${AutoInterfaceOut_SOURCE_DIR}  ${AutoInterfaceOut_SOURCE_DIR}/cmake_local_modules )

MESSAGE( STATUS "MODULE PATH: ${CMAKE_MODULE_PATH}" )

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


"""
        ret = ret + "IF( BUILD_MEX )\n"

        ret = ret + "    find_package( matlab )\n"
        ret = ret + """
# FOR FILE IN MEX_MAT_SUPPORT AND MEXX_CLASS_DEF, set -fPIC
SET_SOURCE_FILES_PROPERTIES( ${MEX_CLASS_DEF} ${MEX_MAT_SUPPORT} PROPERTIES COMPILE_FLAGS "-fPIC" )
ADD_LIBRARY( auto_interface_mat_support SHARED ${MEX_MAT_SUPPORT} ${MEX_CLASS_DEF} mex/props_parser.cpp )
TARGET_LINK_LIBRARIES( auto_interface_mat_support ${MATLAB_LIBRARIES} )
"""




        for struct_name, struct_def in self.structs.items():

            ret = ret + TAB + '# %s\n' % ( struct_name )
            ret = ret + TAB + 'SET_SOURCE_FILES_PROPERTIES( %s COMPILE_FLAGS "-I{MATLAB_PATH}/extern/include -fPIC" )\n' %( struct_name )
            ret = ret + TAB + 'ADD_LIBRARY( %s SHARED mex/%s_mex_impl.cpp )\n' %( struct_name, struct_name )
            ret = ret + TAB + 'SET_TARGET_PROPERTIES( %s PROPERTIES PREFIX "" SUFFIX ".mexmaci64" )\n' % ( struct_name )
            ret = ret + TAB + 'TARGET_LINK_LIBRARIES( %s auto_interface_mat_support )\n\n' % ( struct_name )

        ret = ret + "ENDIF( BUILD_MEX )\n\n"
        
        ret = ret + "IF( BUILD_OCT )\n"


        ret = ret + TAB + "FIND_PACKAGE( octave )\n"


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




        ret = ret + TAB + "LINK_DIRECTORIES( ${OCT_LIBDIRS} )\n"
        ret = ret + TAB + "INCLUDE_DIRECTORIES( ${OCT_INC_DIRS} )\n"

        for struct_name, struct_def in self.structs.items():

            ret = ret + TAB + '# %s\n' % ( struct_name )
            ret = ret + TAB + 'SET_SOURCE_FILES_PROPERTIES( %s_mex_impl COMPILE_FLAGS ${OCT_DEFS} )\n' %( struct_name )
            ret = ret + TAB + 'ADD_LIBRARY( %s_mex_impl SHARED mex/%s_mex_impl.cpp )\n' %( struct_name, struct_name )
            ret = ret + TAB + 'SET_TARGET_PROPERTIES( %s_mex_impl PROPERTIES PREFIX "" SUFFIX ".mex" )\n' % ( struct_name )
            ret = ret + TAB + 'TARGET_LINK_LIBRARIES( %s_mex_impl auto_interface_mat_support ${OCT_LIBS} )\n\n' % ( struct_name )

        ret = ret + "ENDIF( BUILD_OCT )\n"
        

### OCTAVE CMD:
# mkoctfile -v Bar_mex_impl.cpp Bar_class_def.cpp Bar_mat_support.cpp -I.
#g++ -c -fPIC -I/usr/include/octave-3.4.3/octave/.. -I/usr/include/octave-3.4.3/octave -I/usr/include/freetype2 -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -I. Bar_mex_impl.cpp -o Bar_mex_impl.o

### MAT COMMAND:
#g++ -m64 $(INC_DIRS) -DMATLAB_MEX_FILE -fPIC -O2 -shared mex_func.cpp $(LIB_DIRS) $(LIBS) -o mex_func.$(MEX_LIB_SUFFIX)
#
        return ret
    # end create_cmake_lists
    

##################################################################################
#
# Main Driver Functions
#
##################################################################################


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


    def create_struct_impls(self):
        '''Creates all structure and matlab support cpp files'''
        fOut = open( self.src_dir + os.sep + "props_parser.cpp", "w" )
        fOut.write( PROPS_PARSER_C )
        fOut.close()

        fOut = open( self.inc_dir + os.sep + "props_parser.h", "w" )
        fOut.write( PROPS_PARSER_H )
        fOut.close() 

        fOut = open ( self.mex_dir + os.sep + "props_parser.cpp", "w" )
        fOut.write( PROPS_PARSER_C )
        fOut.close()

        fOut = open ( self.mex_dir + os.sep + "props_parser.h", "w" )
        fOut.write( PROPS_PARSER_H )
        fOut.close()

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
        self.cmake_dir = self.out_dir + os.sep + 'cmake_local_modules'
        self.mat_dir = self.out_dir + os.sep + 'mat/'
        for d in self.mex_dir, self.inc_dir, self.src_dir, self.cmake_dir, self.mat_dir:
            if not os.path.exists( d ):
                os.mkdir(d)

        # ----------- path of script file
        python_dir = os.path.dirname(os.path.realpath(__file__))
        cmake_res_dir  = python_dir + '/../cmake_files'
        import shutil
        shutil.copy( cmake_res_dir + '/Findoctave.cmake', self.cmake_dir + '/Findoctave.cmake' )
        shutil.copy( cmake_res_dir + '/Findmatlab.cmake', self.cmake_dir + '/Findmatlab.cmake' )
    # end create_directory_structure


# end AutoGenerator

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
    
