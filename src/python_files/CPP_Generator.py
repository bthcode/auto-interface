##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil
from AutoInterface import AutoGenerator
from GPB_Generator import *


T="    "


stock_includes = \
'''
// Stock Includes
#include <stdlib.h>
#include <cstddef>
#include <stdint.h>
#include <iostream>
#include <string>
#include <map>
#include <complex>
#include <vector>
#include <fstream>
#include <sstream>
#include "props_parser.h"

'''

class_end = \
'''

    // Member Functions
    void write_props( std::ostream& r_stream, std::string& r_prefix );
    int validate( std::string& err_msg );
    void set_defaults();
    void read_props( std::istream& r_in_stream, std::string& r_prefix );
    std::size_t read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix );
    void write_binary( std::ofstream& r_out_stream );
    void read_binary( std::ifstream& r_in_stream );

};
'''



###############################################################
# BEGIN C++
###############################################################
def create_struct_header( basetypes, structs, struct_name,project,gpb=False ):
    '''Creates the Primary Structure Header'''
    struct_def = structs[ struct_name ]
    ret = ''

    ret = ret + "\n/**\n * @brief %s\n */\n" % ( struct_def[ 'DESCRIPTION' ] )

    ### Class Def
    ret = ret + 'class {0}\n{{\n'.format( struct_name )
    ret = ret + T + 'public :\n'
    ret = ret + T + '{0}();\n'.format( struct_name )
    ret = ret + T + '~{0}(){{}};\n'.format( struct_name ) 

    if gpb:
        gpb_namespace = '{0}_GPB'.format(project['NAMESPACE'])
        gpb_classname = struct_def['NAME']
        ret = ret + "\n\n"
        ret = ret + T + "/**\n"
        ret = ret + T + " * @brief GPB Reader\n"
        ret = ret + T + " */\n"
        ret = ret + T + "void read_gpb(const {0}::{1}& gpb_obj);\n\n".format(gpb_namespace,gpb_classname)
        ret = ret + T + "/**\n"
        ret = ret + T + " * @brief GPB Reader\n"
        ret = ret + T + " */\n"
        ret = ret + T + "void write_gpb({0}::{1}* gpb_obj);\n\n".format(gpb_namespace,gpb_classname)

    ### Member Data
    ret = ret + '\n\n    // Member Fields\n\n'
    for f in struct_def['FIELDS']:
        n_elements=''

        # get c type
        if f['IS_BASETYPE']:
            basetype = basetypes[f['TYPE']]
            c_decl = basetype['CPP_TYPE']
        elif f['IS_STRUCT']:
            c_decl = '%s' % ( f['TYPE'] )

        # handle scalar v. array v. vector
        if f['LENGTH'] == 1:
            pass
        elif f['LENGTH'] == 'VECTOR':
            c_decl = 'std::vector< {0} >'.format( c_decl )
        elif type(f['LENGTH']) == int:
            n_elements ='[{0}]'.format(f['LENGTH'])
        else:
            print 'ERROR - vector with no TYPE'
            sys.exit(1)

        # write declaration
        ret = ret + T + "{0}  {1}{2}; ///<{3}\n".format( c_decl, f['NAME'], n_elements,f['DESCRIPTION'] )

    ret = ret + class_end


    return ret
# end create_struct_header

def create_struct_generator( basetypes, structs, struct_name, project ):
    struct_def = structs[ struct_name ]

    ret = '#include "{0}_classes.hpp"\n\n'.format(project['PROJECT'])
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


def create_struct_printer( basetypes, structs, struct_name, project ):
    struct_def = structs[ struct_name ]

    ret = '#include "{0}_classes.hpp"\n\n'.format(project['PROJECT'])
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
    


def create_struct_impl(basetypes,structs,struct_name,project,gpb=False):
    '''Creates the Primary Structure CPP Implementation'''

    struct_def = structs[struct_name]

    ret = ''

    ### Constructor
    ret = ret + '%s::%s(){}\n\n\n' % (struct_name,struct_name)

    ### Read Binary
    ret = ret + "void %s::read_binary( std::ifstream& r_stream ){\n\n" % (struct_name)
    for f in struct_def['FIELDS']:
        # get type
        if f['IS_BASETYPE']:
            basetype = basetypes[f['TYPE']]
            ctype = basetype['CPP_TYPE']
   
        if f['LENGTH']==1:
            if f['IS_BASETYPE']:
                ret = ret + T + 'r_stream.read( (char*)&(%s), sizeof(%s) );\n' %(f['NAME'],f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + '%s.read_binary( r_stream );\n' % (f['NAME'])
        elif type(f['LENGTH']) == int:
            if f['IS_BASETYPE']:
                ret = ret + T + 'r_stream.read( reinterpret_cast<char*>(&{0}[0]), {1} * sizeof({2}));\n'.format(f['NAME'],f['LENGTH'],ctype)
            elif f['IS_STRUCT']:
                ret = ret + T + 'for ( uint32_t ii=0; ii < {0}; ii++ ) {{\n'.format(f['LENGTH'])
                ret = ret + T + T + '{0}[ii].read_binary(r_stream);\n'.format(f['NAME'])
                ret = ret + T + '}\n'

        elif f['LENGTH'] == 'VECTOR':
            ret = ret + T + 'int32_t tmp_%s_size;\n' % (f['NAME'])
            ret = ret + T + 'r_stream.read( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % (f['NAME'],f['NAME'])
            if f['IS_BASETYPE']:
                ret = ret + T + '{0}.resize( tmp_{0}_size );\n'.format(f['NAME'])
                ret = ret + T + 'if (tmp_{0}_size > 0)\n'.format(f['NAME'])
                ret = ret + T + T + 'r_stream.read( reinterpret_cast<char*>(&{0}[0]), tmp_{0}_size * sizeof({1}));\n'.format(f['NAME'],ctype)
            elif f['IS_STRUCT']:
                ctype = f['TYPE']
                ret = ret + T + 'for ( uint32_t ii=0; ii < tmp_%s_size; ii++ ) {\n' % (f['NAME'])
                ret = ret + T + T + '%s tmp_%s;\n' % (ctype,ctype)
                ret = ret + T + T + 'tmp_%s.read_binary( r_stream );\n' % (ctype)
                ret = ret + T + T + '%s.push_back( tmp_%s );\n' % (f['NAME'],ctype)
                ret = ret + T + '}\n'
    ret = ret + "}\n\n"


    ### Write Binary
    ret = ret + "void %s::write_binary( std::ofstream& r_stream ){\n\n" % (struct_name)
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + 'r_stream.write( (char*)&(%s), sizeof(%s) );\n' %(f['NAME'],f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + '%s.write_binary( r_stream );\n' % (f['NAME'])
        # TODO: duplicate code
        elif type(f['LENGTH']) == int:
            # TODO: this write should be faster
            if f['IS_BASETYPE']:
                ret = ret + T + 'for ( uint32_t ii=0; ii < {0}; ii++ ) {{\n'.format(f['LENGTH'])
                ret = ret + T + T + 'r_stream.write( (char*)&(%s[ii]), sizeof(%s[ii]));\n' % (f['NAME'],f['NAME'])
                ret = ret + T + '}\n'
            elif f['IS_STRUCT']:
                ret = ret + T + 'for ( uint32_t ii=0; ii < {0}; ii++ ) {{\n'.format(f['LENGTH'])
                ret = ret + T + T + '{0}[ii].write_binary( r_stream );\n'.format(f['NAME'])
                ret = ret + T + '}\n'
        elif f['LENGTH'] == 'VECTOR':
            ret = ret + T + 'int32_t tmp_%s_size = %s.size();\n' % (f['NAME'],f['NAME'])
            ret = ret + T + 'r_stream.write( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % (f['NAME'],f['NAME'])
            # TODO: This write should be faster
            if f['IS_BASETYPE']:
                ret = ret + T + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % (f['NAME'])
                ret = ret + T + T + 'r_stream.write( (char*)&(%s[ii]), sizeof(%s[ii]));\n' % (f['NAME'],f['NAME'])
                ret = ret + T + '}\n'
            elif f['IS_STRUCT']:
                ret = ret + T + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % (f['NAME'])
                ret = ret + T + T + '%s[ii].write_binary( r_stream );\n' % (f['NAME'])
                ret = ret + T + '}\n'
    ret = ret + "}\n\n"



    ### Write Props
    ret = ret + "void %s::write_props( std::ostream& r_stream, std::string& r_prefix ){\n\n" % (struct_name)
    ret = ret + T + "std::string tmp;\n"
    for f in struct_def['FIELDS']:
        if f['LENGTH']==1:
            if f['IS_BASETYPE']:
                b = basetypes[ f['TYPE'] ]
                c_print = T + 'r_stream << r_prefix << "%s = " << (%s)(%s) << "\\n";\n' % (f['NAME'],b['STREAM_CAST'],f['NAME'])
                ret = ret + c_print
            elif f['IS_STRUCT']:
                ret = ret + T + 'tmp = r_prefix + "%s.";\n' % (f['NAME'])
                c_print = T + '%s.write_props( r_stream, tmp );\n' % (f['NAME'])
                ret = ret + c_print
        elif type(f['LENGTH']) == int:
            if f['IS_BASETYPE']:
                b = basetypes[ f['TYPE'] ]
                ret = ret + T + 'r_stream << r_prefix << "{0}" <<  " = " ;\n'.format(f['NAME'])
                ret = ret + T + 'for ( std::size_t ii = 0; ii != {1}; ii++ )\n'.format(f['NAME'],f['LENGTH'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'r_stream << ({0})({1}[ii]) << " ";'.format(b['STREAM_CAST'],f['NAME'])
                ret = ret + T + '}\n'
                ret = ret + T + 'r_stream << std::endl;\n'
            elif f['IS_STRUCT']:
                ret = ret + T + T +  'for ( std::size_t ii = 0; ii != {0}; ii++ )\n'.format(f['LENGTH'])
                ret = ret + T + T +  '{\n'
                # Build a prefix
                ret = ret + T + T + T + 'std::stringstream ss;\n'
                ret = ret + T + T + T + 'ss << r_prefix << "{0}[ " << ii << " ].";\n'.format(f['NAME'])
                ret = ret + T + T + T + 'std::string tmp( ss.str() );\n'
                # Use prefix to write props
                ret = ret + T + T + T + '{0}[ii].write_props( r_stream, tmp );\n'.format(f['NAME'])
                ret = ret + T + T +  '}\n'
        elif f['LENGTH'] == 'VECTOR':
            if f['IS_BASETYPE']:
                b = basetypes[ f['TYPE'] ]
                ret = ret + T + 'r_stream << r_prefix << "{0}" <<  " = " ;\n'.format(f['NAME'])
                ret = ret + T + 'for ( std::size_t ii = 0; ii != {0}.size(); ii++ )\n'.format(f['NAME'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'r_stream << ({0})({1}[ii]) << " ";'.format(b['STREAM_CAST'],f['NAME'])
                ret = ret + T + '}\n'
                ret = ret + T + 'r_stream << std::endl;\n'
            elif f['IS_STRUCT']:
                iter_decl = T + T + 'std::vector< %s >::iterator ii;\n' % (f['TYPE'])
                print_decl = T + T + T + 'std::stringstream ss;\n'
                print_decl = print_decl + T + T + T + 'ss << r_prefix << "%s[ " << count << " ].";\n' % (f['NAME'])
                print_decl = print_decl + T + T + T + 'std::string tmp( ss.str() );\n'
                print_decl = print_decl + T + T + T + 'ii->write_props( r_stream, tmp );\n'
            
                ret = ret + T + '{\n'
                ret = ret + iter_decl
                ret = ret + T + T +  'std::size_t count = 0;\n'
                ret = ret + T + T +  'for ( ii = %s.begin(); ii != %s.end(); ii++ )\n' %(f['NAME'],f['NAME'])
                ret = ret + T + T +  '{\n'
                ret = ret + print_decl
                ret = ret + T + T +T +   'count++;\n'
                ret = ret + T + T +  '}\n'
                ret = ret + T + '}\n'
    ret = ret + "}\n\n"

    ### Read Props From Params
    ret = ret + "std::size_t %s::read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix ){\n\n" % (struct_name)
    ret = ret + T + 'std::string key;\n'
    ret = ret + T + 'std::map< std::string, std::string >::iterator param_iter;\n'
    ret = ret + T + 'std::size_t fields_found=0;\n'

    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + 'key = r_prefix + "%s";\n\n' % (f['NAME'])
                ret = ret + T + 'param_iter = r_params.find( key );\n'
                ret = ret + T + 'if ( param_iter != r_params.end() )\n'
                ret = ret + T + '{\n'
                ret = ret + T +T +  'std::stringstream ss( param_iter->second );\n'
                ret = ret + T +T +  '%s u;\n' % (b['STREAM_CAST'])
                ret = ret + T +T +  'ss >> u;\n'
                ret = ret + T +T +  '%s = (%s)( u );\n' % (f['NAME'],b['STREAM_CAST'])
                ret = ret + T +T +  'fields_found++;\n'
                ret = ret + T + '}\n'
            elif f['IS_STRUCT']:
                ret = ret + T + 'key = r_prefix + "%s.";\n' % (f['NAME'])
                ret = ret + T + 'fields_found += %s.read_props( r_params, key );\n' % (f['NAME'])
        elif type( f['LENGTH'] ) == int:
            # TODO
            pass
        elif f['LENGTH'] == 'VECTOR':
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + 'key = r_prefix + "%s";\n\n' % (f['NAME'])
                ret = ret + T + 'param_iter = r_params.find( key );\n'
                ret = ret + T + 'if ( param_iter != r_params.end() )\n'
                ret = ret + T + '{\n'
                ret = ret + T + T + '%s.clear();\n' % ( f['NAME'] )
                ret = ret + T + T + 'std::stringstream ss( param_iter->second );\n'
                ret = ret + T + T + '%s u;\n' % ( b[ 'STREAM_CAST' ] )
                ret = ret + T + T + 'while( ss >> u ) %s.push_back( u );\n' % ( f['NAME'] )
                ret = ret + T + T + 'fields_found++;\n'
                ret = ret + T + '}\n'

            elif f['IS_STRUCT']:
                ret = ret + T + '{\n'
                ret = ret + T + 'std::size_t count=0;\n'
                ret = ret + T + 'while( 1 )\n'
                ret = ret + T + '{\n'
                ret = ret + T + T + 'std::stringstream ss;\n'
                ret = ret + T + T + 'ss << r_prefix << "%s" << "[ " << count << " ].";\n' % ( f['NAME'] )
                ret = ret + T + T + '%s tmp_%s;\n' % (f['TYPE'],f['TYPE'])
                ret = ret + T + T + 'tmp_%s.set_defaults();\n' % (f['TYPE'])
                ret = ret + T + T + 'std::string s ( ss.str() );\n'
                ret = ret + T + T + 'if ( tmp_%s.read_props( r_params, s )) {\n' % (f['TYPE'])
                ret = ret + T + T + T + '%s.push_back( tmp_%s );\n' % (f['NAME'],f['TYPE'])
                ret = ret + T + T + '}\n'
                ret = ret + T + T +  'else { break; }\n'
                ret = ret + T + T + T + 'count++;\n'
                ret = ret + T + T + '}\n'
                ret = ret + T + 'fields_found += count;\n'
                ret = ret + T + '}\n'
            
    ret = ret + T + 'return fields_found;\n'
    ret = ret + "}\n\n"


    ### Read Props From Stream
    ret = ret + "void %s::read_props( std::istream& r_in_stream, std::string& r_prefix ){\n\n" % (struct_name)
    ret = ret + T + 'std::map< std::string, std::string > params;\n\n'
    ret = ret + T + 'parse_param_stream( r_in_stream, params );\n\n' 
    ret = ret + T + 'std::string key;\n'
    ret = ret + T + 'read_props( params, r_prefix );\n' 
    ret = ret + "}\n\n"

    ### Defaults
    ret = ret + "void %s::set_defaults( ){\n\n" % (struct_name)
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[ f['TYPE'] ]
                # get default value
                def_val = f['DEFAULT_VALUE']
                # format for complex or not
                if b['IS_COMPLEX']:
                    val = '{0}({1},{2})'.format(b['CPP_TYPE'],def_val[0],def_val[1])
                else:
                    val = '{0}'.format(def_val)
                # set default value
                ret = ret + T + '{0} = {1};\n'.format(f['NAME'],val)
            elif f['IS_STRUCT']:
                ret = ret + T + '%s.set_defaults( );\n' % ( f['NAME'] )
        elif type(f['LENGTH']) == int:
            # TODO
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                # get default value
                def_val = f['DEFAULT_VALUE']
                # format for complex or not
                if b['IS_COMPLEX']:
                    num_elements = len(def_val)/2
                    counter=0
                    for idx in range(0,len(def_val)):
                        ret = ret + T + '{0}[{1}] = {2}({3},{4});\n'.format(f['NAME'],
                                                                            counter,
                                                                            b['CPP_TYPE'],
                                                                            def_val[idx][0],
                                                                            def_val[idx][1])
                        counter = counter+1
                else:
                    num_elements = len(def_val)
                    counter=0
                    for idx in range(len(def_val)):
                        ret = ret + T + '{0}[{1}] = {2};\n'.format(f['NAME'],counter,def_val[idx])
                        counter = counter+1
            elif f['IS_STRUCT']:
                ret = ret + T + 'for ( std::size_t ii=0; ii < {0}; ii++ )\n'.format( f['LENGTH'] )
                ret = ret + T + '{\n'
                ret = ret + T + T + '{0}[ii].set_defaults();\n'.format(f['NAME'])
                ret = ret + T + '}\n'

        elif f['LENGTH'] == 'VECTOR':
            if f.has_key('DEFAULT_VALUE'):
                if f['IS_BASETYPE']:
                    b = basetypes[f['TYPE']]
                    # get default value
                    if f.has_key('DEFAULT_VALUE'):
                        def_val = f['DEFAULT_VALUE']
                    # format for complex or not
                    if b['IS_COMPLEX']:
                        num_elements = len(def_val)/2
                        ret = ret + T + '{0}.resize({1});\n'.format(f['NAME'],num_elements)
                        counter=0
                        for idx in range(0,len(def_val),2):
                            ret = ret + T + '{0}[{1}] = {2}({3},{4});\n'.format(f['NAME'],
                                                                                counter,
                                                                                b['CPP_TYPE'],
                                                                                def_val[idx],
                                                                                def_val[idx+1])
                            counter = counter+1
                    else:
                        num_elements = len(def_val)
                        ret = ret + T + '{0}.resize({1});\n'.format(f['NAME'],num_elements)
                        counter=0
                        for idx in range(len(def_val)):
                            ret = ret + T + '{0}[{1}] = {2};\n'.format(f['NAME'],counter,def_val[idx])
                            counter = counter+1

                elif f['IS_STRUCT']:
                    pass
                else:
                    print ("Unknown vector type: {0}".format(f['TYPE']))
            else:
                ret = ret + T + '{0}.resize(0);\n'.format(f['NAME'])
    ret = ret + "}\n\n"

    ### Validate 
    ret = ret + "int %s::validate( std::string& err_msg ){\n\n" % ( struct_name )
    ret = ret + T + "int num_errs=0;\n"
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[ f['TYPE'] ]
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
            elif f['IS_STRUCT']:
                ret = ret + T + 'num_errs += %s.validate( err_msg );\n' % ( f['NAME'] )
    ret = ret + T + 'return num_errs;\n';
    ret = ret + "}\n\n"

    ### Read GPB
    if gpb:
        gpb_namespace = '{0}_GPB'.format(project['NAMESPACE'])
        gpb_classname = struct_def['NAME']
        class_name    = struct_def['NAME']
        ret = ret + "void {0}::read_gpb(const {1}::{2}& gpb_obj){{\n".format(class_name,gpb_namespace,gpb_classname)
        ret = ret + T + 'int max_count;\n'
        for f in struct_def['FIELDS']:
            field    = f['NAME']
            # need max count for fixed length fields
            if type(f['LENGTH']) == int and f['LENGTH'] > 1:
                ret = ret + T + 'max_count = std::min({0}, gpb_obj.{1}_size());\n'.format(f['LENGTH'],field)
            elif f['TYPE'] == 'VECTOR':
                ret = ret + T + 'max_count = {0}->{1}_size();\n'.format(gpb_obj,field)
                ret = ret + T + '{0}.resize(max_count);\n'.format(field)
            # get type
            if f['IS_BASETYPE']:
                basetype = basetypes[f['TYPE']]
                gpb_type = basetype['GPB_TYPE']
                #ctype = basetype['CPP_TYPE']
            if f['LENGTH']==1:
                if f['IS_BASETYPE']:
                    ret = ret + T + 'if (gpb_obj.has_{0}()){{\n'.format(field)
                    ret = ret + T + T + 'this->{0} = gpb_obj.{0}();\n'.format(field)
                    ret = ret + T + '}\n'
                elif f['IS_STRUCT']:
                    ret = ret + T + 'if (gpb_obj.has_{0}()){{\n'.format(field)
                    ret = ret + T + T + '{0}.read_gpb(gpb_obj.{0}());\n'.format(field)
                    ret = ret + T + '}\n'
            elif type(f['LENGTH']) == int or f['LENGTH'] == 'VECTOR':
                if f['IS_BASETYPE']:
                    ret = ret + T + 'for (int ii=0; ii < max_count; ii++ ){\n'
                    ret = ret + T + T + '{0}[ii] = ({1}) gpb_obj.{0}(ii);\n'.format(field,ctype)
                    ret = ret + T + '}\n'
                elif f['IS_STRUCT']:
                    ret = ret + T + 'for (int ii=0; ii < max_count; ii++ ){\n'
                    ret = ret + T + T + '{0} tmp_{0};\n'.format(f['TYPE'])
                    ret = ret + T + T + 'tmp_{0}.read_gpb(gpb_obj.{1}(ii));\n'.format(f['TYPE'],field)
                    ret = ret + T + T + '{0}[ii] = tmp_{1};\n'.format(field,f['TYPE'])
                    ret = ret + T + '}\n'
        ret = ret + "}\n\n"

        ret = ret + "void {0}::write_gpb({1}::{2}* gpb_obj){{\n".format(class_name,gpb_namespace,gpb_classname)
        ret = ret + T + 'int max_count;\n'
        for f in struct_def['FIELDS']:
            field    = f['NAME']
            if f['IS_BASETYPE']:
                basetype = basetypes[f['TYPE']]
                gpb_type = basetype['GPB_TYPE']
                #ctype = basetype['CPP_TYPE']
            if f['LENGTH']==1:
                if f['IS_BASETYPE']:
                    default = f['DEFAULT_VALUE']
                    ret = ret + T + 'if ({0} != {1}){{\n'.format(field,default)
                    ret = ret + T + T + 'gpb_obj->set_{0}({0});\n'.format(field)
                    ret = ret + T + '}\n'
                elif f['IS_STRUCT']:
                    ret = ret + T + '{0}.write_gpb(gpb_obj->mutable_{0}());\n'.format(field)
            elif type(f['LENGTH']) == int:
                if f['IS_BASETYPE']:
                    ret = ret + T + 'for (int ii=0; ii < {0}; ii++ ){{\n'.format(f['LENGTH'])
                    ret = ret + T + T + 'gpb_obj->add_{0}({0}[ii]);\n'.format(field)
                    ret = ret + T + '}\n'
                elif f['IS_STRUCT']:
                    ret = ret + T + 'for (int ii=0; ii < {0}; ii++ ){{\n'.format(f['LENGTH'])
                    ret = ret + T + T + '{0}::{1} * tmp = gpb_obj->add_{2}();;\n'.format(gpb_namespace,f['TYPE'],field)
                    ret = ret + T + T + '{0}[ii].write_gpb(tmp);\n'.format(field)
                    ret = ret + T + '}\n'
        ret = ret + "}\n\n"

    return ret
# end create_struct_impl

def create_cmake_file( cpp_src_dir, cpp_inc_dir, basetypes, structs, project, gpb=False ):
    proj_name=project['PROJECT']
    ret = """
cmake_minimum_required(VERSION 2.8)

PROJECT({0})

SET( CMAKE_VERBOSE_MAKEFILE ON )

SET( CMAKE_INSTALL_PREFIX "./install" )

SET( AUTOGEN_SRC_DIR  "{1}" )
SET( AUTOGEN_INC_DIR  "{2}" )

# Basic Library
#FILE( GLOB CPP_FILES "*_class_def.cpp" "props_parser.cpp"  )
SET( CPP_FILES "{0}_classes.cpp" "props_parser.cpp" )

########### VERBOSE DEBUG ##########
MESSAGE( STATUS "CPP_FILES:" )
FOREACH( loop_var ${{CPP_FILES}} )
    MESSAGE( STATUS "  ${{loop_var}}" )
ENDFOREACH()
########### VERBOSE DEBUG ##########
""".format( proj_name,cpp_src_dir, cpp_inc_dir )

    # Add rules for building protocol buffers bindings
    if gpb:
        gpb_links = 'protobuf'
        ret = ret + '''
FILE( GLOB GPB_FILES "*.pb.h" "*.pb.cc" )
'''
    else:
        gpb_links = ''
        ret = ret + '\nSET( GPB_FILES "" )\n\n'

    ret = ret + '\nADD_LIBRARY( {0}_classes ${{CPP_FILES}} ${{GPB_FILES}} )\n\n'.format(proj_name)

    # Sample executables


    for struct_name, struct_def in structs.items():
        ret = ret + 'ADD_EXECUTABLE( print_{0} print_{0}.cpp )\n'.format(struct_name)
        ret = ret + 'TARGET_LINK_LIBRARIES( print_{0} {1}_classes {2} )\n\n'.format(struct_name,proj_name,gpb_links) 

        ret = ret + 'ADD_EXECUTABLE( generate_{0} generate_{0}.cpp )\n'.format(struct_name)
        ret = ret + 'TARGET_LINK_LIBRARIES( generate_{0} {1}_classes {2} )\n\n'.format(struct_name,proj_name,gpb_links) 




    return ret

# end create_cmake_file


##################################################################################
#
# Main Driver Functions
#
##################################################################################

def generate_CPP( cpp_src_dir, cpp_inc_dir, basetypes, structs, project, gpb=False ):
    if not os.path.exists( cpp_src_dir ):
        os.mkdir(cpp_src_dir)
    if not os.path.exists( cpp_inc_dir ):
        os.mkdir(cpp_inc_dir)

    python_repo_dir = os.path.dirname(os.path.realpath(__file__))

    # utils
    shutil.copy( python_repo_dir + os.sep + 'props_parser.cpp', 
                 cpp_src_dir + os.sep + 'props_parser.cpp' )

    shutil.copy( python_repo_dir + os.sep + 'props_parser.h', 
                 cpp_inc_dir + os.sep + 'props_parser.h' )

    # proto file
    if gpb:
        print ("Creating GPB Proto File")
        proto_file = generate_gpb(cpp_src_dir,cpp_inc_dir,basetypes,structs,project)
        proto_file = os.path.split(proto_file)[-1]
        # Call protoc - need to be in the directory with it
        here = os.getcwd()
        os.chdir(cpp_src_dir)
        cmd = '''protoc --cpp_out={0} {1}'''.format('.',proto_file)
        print ("Calling {0}".format(cmd))
        os.popen(cmd)
        os.chdir(here)

    #-----------------------------------------------------
    # Start Headers
    #-----------------------------------------------------
    header_file_name = '{0}_classes.hpp'.format(project['PROJECT'])
    fOut = open( cpp_inc_dir + os.sep + header_file_name, "w" )

    #HEADER Guards
    fOut.write('#ifndef {0}_classes_H\n'.format(project['PROJECT']))
    fOut.write('#define {0}_classes_H\n'.format(project['PROJECT']))
    fOut.write(stock_includes)

    if gpb:
        fOut.write('#include "{0}_structs.pb.h"\n'.format(project['PROJECT']))

    fOut.write('namespace {0} {{\n'.format(project['NAMESPACE']))
    for struct_name, struct_def in structs.items():
        fOut.write( create_struct_header(basetypes,structs,struct_name,project,gpb)) 

    ### End Namespace
    fOut.write('} // namepsace\n\n')
    fOut.write('#endif // Header Guard\n' )
    fOut.close()
    #-----------------------------------------------------
    # End Headers
    #-----------------------------------------------------

    #-----------------------------------------------------
    # Start Impls
    #-----------------------------------------------------
    impl_file_name = '{0}_classes.cpp'.format(project['PROJECT']) 
    fOut = open( cpp_inc_dir + os.sep + impl_file_name, "w" )
    fOut.write('#include "{0}"\n'.format(header_file_name))

    fOut.write('namespace {0} {{\n'.format(project['NAMESPACE']))
    for struct_name, struct_def in structs.items():
        class_def = create_struct_impl(basetypes, structs, struct_name,project,gpb) 
        fOut.write( class_def )

    fOut.write('} // namepsace\n\n')
    fOut.close()
    #-----------------------------------------------------
    # End Impls
    #-----------------------------------------------------

    # printers
    for struct_name, struct_def in structs.items():
        fOut = open( cpp_src_dir + os.sep + "print_%s.cpp" % (struct_name), "w" )
        fOut.write( create_struct_printer(basetypes,structs,struct_name,project)) 

    # generators
    for struct_name, struct_def in structs.items():
        fOut = open( cpp_src_dir + os.sep + "generate_%s.cpp" % (struct_name), "w" )
        fOut.write( create_struct_generator(basetypes,structs,struct_name,project)) 

    cmake_txt = create_cmake_file( cpp_src_dir, cpp_inc_dir, basetypes, structs, project, gpb )
    fOut = open( cpp_src_dir + os.sep + "CMakeLists.txt", "w" )
    fOut.write( cmake_txt )


# end generate_CPP


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'inc_dir' )
    parser.add_argument( 'src_dir' )
    parser.add_argument( '--gpb', action='store_true', help='If selected, generate google protocol buffers serializer')
    parser.add_argument( '--pad', default=8, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    A = AutoGenerator( args.json_basetypes_file, args.json_structures_file,pad=args.pad)
    basetypes = A.basetypes
    structs   = A.structs
    project   = A.project

    generate_CPP( args.src_dir, args.inc_dir, basetypes, structs,project,gpb=args.gpb )
