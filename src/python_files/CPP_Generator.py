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

def get_dependencies_for_struct(structs, struct_name):
    includes = {} # insert into a map to force unique -- probably a better way
    struct_def = structs[ struct_name ]
    for field in struct_def['FIELDS']:
        if field['TYPE'] == "STRUCT":
            includes[ "%s_class_def.h" % ( field['STRUCT_TYPE'] ) ] = 1
        elif  field['TYPE'] == 'VECTOR' and field['CONTAINED_TYPE'] == 'STRUCT':
            includes[ "%s_class_def.h" % ( field['STRUCT_TYPE'] ) ] = 1
    return includes.keys()
# end get_dependencies_for_struct

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
    std::size_t num_fields;

    // Member Functions
    void write_props( std::ostream& r_stream, std::string& r_prefix );
    int validate( std::string& err_msg );
    void set_defaults();
    void read_props( std::istream& r_in_stream, std::string& r_prefix );
    std::size_t read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix );
    void write_binary( std::ofstream& r_out_stream );
    void read_binary( std::ifstream& r_in_stream );

};'''



###############################################################
# BEGIN C++
###############################################################
def create_struct_header( basetypes, structs, struct_name ):
    '''Creates the Primary Structure Header'''
    struct_def = structs[ struct_name ]

    ### HEADER Guards
    ret = '#ifndef {0}_H\n'.format( struct_name )
    ret = ret + '#define {0}_H\n'.format( struct_name )
    ret = ret + stock_includes

    ### Other generated deps
    deps = get_dependencies_for_struct( structs, struct_name )
    for dep in deps:
        ret = ret + '#include "%s"' % dep + "\n"

    ### Namespace
    if struct_def.has_key( 'NAMESPACE'  ):
        ret = ret + '\nnamespace %s {\n\n' % ( struct_def[ 'NAMESPACE' ] )

    ret = ret + "\n/**\n * @brief %s\n */\n" % ( struct_def[ 'DESCRIPTION' ] )

    ### Class Def
    ret = ret + 'class {0}\n{{\n'.format( struct_name )
    ret = ret + T + 'public :\n'
    ret = ret + T + '{0}();\n'.format( struct_name )
    ret = ret + T + '~{0}(){{}};\n'.format( struct_name ) 


    ### Member Data
    ret = ret + '\n\n    // Member Fields\n\n'
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            basetype = basetypes[f['TYPE']]
            if basetype.has_key( 'CPP_TYPE' ):
                c_decl = basetype['CPP_TYPE']
            else:
                c_decl = basetypes[ f['TYPE'] ]['C_TYPE']
        elif f['TYPE'] == 'STRUCT':
            c_decl = '%s' % ( f['STRUCT_TYPE'] )
        elif f['TYPE'] == 'VECTOR':
            if f['CONTAINED_TYPE'] == 'STRUCT':
                c_decl = 'std::vector< %s >' % ( f['STRUCT_TYPE'] )
            elif basetypes.has_key( f['CONTAINED_TYPE'] ):
                c_decl = 'std::vector< %s >' % ( basetypes[ f['CONTAINED_TYPE'] ][ 'C_TYPE' ] )
            else:
                print 'ERROR - vector with unknown type or no CONTAINED_TYPE key'
                sys.exit(1)
        else:
            print 'ERROR - vector with no TYPE'
            sys.exit(1)
        ret = ret + T + "%s  %s; ///<%s\n" % ( c_decl, f['NAME'], f['DESCRIPTION'] )

    ret = ret + class_end

    ### End Namespace
    if struct_def.has_key( 'NAMESPACE' ):
        ret = ret + '} // namepsace\n\n'


    ret = ret + "#endif\n"
    return ret
# end create_struct_header

def create_struct_generator( basetypes, structs, struct_name ):
    struct_def = structs[ struct_name ]

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


def create_struct_printer( basetypes, structs, struct_name ):
    struct_def = structs[ struct_name ]

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
    


def create_struct_impl( basetypes, structs, struct_name ):
    '''Creates the Primary Structure CPP Implementation'''

    struct_def = structs[ struct_name ]

    ret = '#include "%s_class_def.h"\n\n' % ( struct_name )

    ### Namespace
    if struct_def.has_key( 'NAMESPACE'  ):
        ret = ret + '\nnamespace %s {\n\n' % ( struct_def[ 'NAMESPACE' ] )

    ### Constructor
    ret = ret + '%s::%s() : num_fields(%s){}\n\n\n' % ( struct_name, struct_name, len( struct_def['FIELDS'] ) )

    ### Read Binary
    ret = ret + "void %s::read_binary( std::ifstream& r_stream ){\n\n" % ( struct_name )
    for f in struct_def['FIELDS']:
        if basetypes.has_key(f['TYPE']):
            ret = ret + T + 'r_stream.read( (char*)&(%s), sizeof(%s) );\n' %( f['NAME'], f['NAME'] )
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + '%s.read_binary( r_stream );\n' % ( f['NAME'] )
        elif f['TYPE'] == 'VECTOR':
            ret = ret + T + 'uint32_t tmp_%s_size;\n' % ( f['NAME'] )
            ret = ret + T + 'r_stream.read( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % ( f['NAME'], f['NAME'] )
            if basetypes.has_key( f['CONTAINED_TYPE'] ):
                # TODO: replace for loop with one big read  
                basetype = basetypes[f['CONTAINED_TYPE']]
                if basetype.has_key('CPP_TYPE'):
                    ctype = basetypes[ f['CONTAINED_TYPE'] ]['CPP_TYPE']
                else:
                    ctype = basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
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
    ret = ret + "}\n\n"


    ### Write Binary
    ret = ret + "void %s::write_binary( std::ofstream& r_stream ){\n\n" % ( struct_name )
    for f in struct_def['FIELDS']:
        if basetypes.has_key(f['TYPE']):
            ret = ret + T + 'r_stream.write( (char*)&(%s), sizeof(%s) );\n' %( f['NAME'], f['NAME'] )
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + '%s.write_binary( r_stream );\n' % ( f['NAME'] )
        elif f['TYPE'] == 'VECTOR':
            ret = ret + T + 'uint32_t tmp_%s_size = %s.size();\n' % ( f['NAME'], f['NAME'] )
            ret = ret + T + 'r_stream.write( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % ( f['NAME'], f['NAME'] )
            if basetypes.has_key(f['CONTAINED_TYPE']):
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
        if basetypes.has_key( f['TYPE'] ):
            b = basetypes[ f['TYPE'] ]
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
            if basetypes.has_key( f['CONTAINED_TYPE'] ):
                b = basetypes[ f['CONTAINED_TYPE'] ]
                iter_decl  = T + T + 'std::vector< %s >::iterator ii;\n' % ( b['C_TYPE'] )
                if b.has_key( 'STREAM_CAST' ):
                    print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << %s((*ii)) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'] )
                else:
                    print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << (*ii) << "\\n";\n' % ( f['NAME'] )
            elif f['CONTAINED_TYPE'] == 'COMPLEX':
                b = basetypes[ f['COMPLEX_TYPE'] ]
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
        if basetypes.has_key( f['TYPE'] ):
            b = basetypes[ f['TYPE'] ]
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
            if basetypes.has_key( f['CONTAINED_TYPE'] ):
                # 1. Get the prefix
                # 2. Go into a while loop incrementing count until no more keys 
                #       are found
                b = basetypes[ f['CONTAINED_TYPE'] ]
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
                b = basetypes[ f['COMPLEX_TYPE'] ]
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
        if basetypes.has_key( f['TYPE'] ):
            b = basetypes[ f['TYPE'] ]
            if f.has_key('DEFAULT_VALUE'):
                ret = ret + T + "%s = %s;\n" % ( f['NAME'], f['DEFAULT_VALUE'] )
            else:
                ret = ret + T + "%s = %s;\n" % ( f['NAME'], b['DEFAULT_VALUE'] )
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + '%s.set_defaults( );\n' % ( f['NAME'] )
        elif f['TYPE'] == 'VECTOR':
            if f.has_key( 'DEFAULT_VALUE' ):
                arr = f['DEFAULT_VALUE'].split()
                ret = ret + T + "{0}.resize( {1} );\n".format( f['NAME'], len(arr) )
                for i, val in enumerate(arr):
                    ret = ret + T + "{0}[{1}] = {2};\n".format( f['NAME'], i, val )
    ret = ret + "}\n\n"

    ### Validate 
    ret = ret + "int %s::validate( std::string& err_msg ){\n\n" % ( struct_name )
    ret = ret + T + "int num_errs=0;\n"
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
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
# Main Driver Functions
#
##################################################################################

def generate_CPP( c_files_res_dir, cpp_src_dir, cpp_inc_dir, basetypes, structs ):
    if not os.path.exists( cpp_src_dir ):
        os.mkdir(cpp_src_dir)
    if not os.path.exists( cpp_inc_dir ):
        os.mkdir(cpp_inc_dir)

    # utils
    shutil.copy( c_files_res_dir + os.sep + 'props_parser.cpp', 
                 cpp_src_dir + os.sep + 'props_parser.cpp' )

    shutil.copy( c_files_res_dir + os.sep + 'props_parser.h', 
                 cpp_inc_dir + os.sep + 'props_parser.h' )

    # headers
    for struct_name, struct_def in structs.items():
        fOut = open( cpp_inc_dir + os.sep + "%s_class_def.h" % (struct_name), "w" )
        fOut.write( create_struct_header(basetypes,structs,struct_name)) 

    # class files
    for struct_name, struct_def in structs.items():
        class_def = create_struct_impl(basetypes, structs, struct_name) 
        fOut = open( cpp_src_dir + os.sep + "%s_class_def.cpp" % (struct_name), "w" )
        fOut.write( class_def )

    # printers
    for struct_name, struct_def in structs.items():
        fOut = open( cpp_src_dir + os.sep + "print_%s.cpp" % (struct_name), "w" )
        fOut.write( create_struct_printer(basetypes,structs,struct_name)) 

    # generators
    for struct_name, struct_def in structs.items():
        fOut = open( cpp_src_dir + os.sep + "generate_%s.cpp" % (struct_name), "w" )
        fOut.write( create_struct_generator(basetypes,structs,struct_name)) 


# end generate_CPP


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'res_dir' )
    parser.add_argument( 'inc_dir' )
    parser.add_argument( 'src_dir' )
    args = parser.parse_args()

    A = AutoGenerator( args.json_basetypes_file, args.json_structures_file, "")
    basetypes = A.basetypes
    structs   = A.structs
    generate_CPP( args.res_dir, args.src_dir, args.inc_dir, basetypes, structs )
