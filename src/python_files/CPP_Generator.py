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
#include "json.hpp"
'''

class_end = \
'''

    // Member Functions
    int validate( std::string& err_msg );
    void set_defaults();
    void write_binary( std::ofstream& r_out_stream );
    void read_binary( std::ifstream& r_in_stream );


}};
    void to_json( nlohmann::json& j, const {0}& p);
    void from_json( const nlohmann::json& obj, {0}& p);

'''



###############################################################
# BEGIN C++
###############################################################
def create_struct_header( basetypes, structs, struct_name,project ):
    '''Creates the Primary Structure Header'''
    struct_def = structs[ struct_name ]
    ret = ''

    ret = ret + "\n/**\n * @brief %s\n */\n" % ( struct_def[ 'DESCRIPTION' ] )

    ### Class Def
    ret = ret + 'class {0}\n{{\n'.format( struct_name )
    ret = ret + T + 'public :\n'
    ret = ret + T + '{0}();\n'.format( struct_name )
    ret = ret + T + '~{0}(){{}};\n'.format( struct_name ) 

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
            print ('ERROR - vector with no TYPE')
            sys.exit(1)

        # write declaration
        ret = ret + T + "{0}  {1}{2}; ///<{3}\n".format( c_decl, f['NAME'], n_elements,f['DESCRIPTION'] )

    ret = ret + class_end.format(struct_name)


    return ret
# end create_struct_header

def create_struct_generator( basetypes, structs, struct_name, project ):
    struct_def = structs[ struct_name ]

    ret = '#include "{0}_classes.hpp"\n\n'.format(project['PROJECT'])
    ret = ret + '#include <iostream>\n'
    ret = ret + '#include <fstream>\n'

    ### Namespace
    if 'NAMESPACE' in struct_def:
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
    if 'NAMESPACE' in struct_def:
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
    ret = ret + T + 'nlohmann::json j;\n'
    ret = ret + T + 'j=tmp;\n'
    ret = ret + T + 'std::cout << j << std::endl;;\n'
    ## READ IN DATA
    ret = ret + T + 'return 0;\n'
    ret = ret + '}\n'
    return ret

def create_json_reader( basetypes, structs, struct_name, project ):
    struct_def = structs[ struct_name ]

    ret = '#include "{0}_classes.hpp"\n\n'.format(project['PROJECT'])
    ret = ret + '#include <iostream>\n'
    ret = ret + '#include <fstream>\n'
    ret = ret + '#include <string>\n'

    ### Namespace
    if 'NAMESPACE' in struct_def:
        ret = ret + '\n using %s::%s;\n' %( struct_def[ 'NAMESPACE' ], struct_name )

    ret = ret + 'int main( int argc, char* argv[] ) {\n'
    ret = ret + T + 'if (argc != 2) {\n'
    ret = ret + T + T + 'std::cout << "USAGE: print_%s < binfile >" << std::endl;\n' % struct_name
    ret = ret + T + T + 'exit(1);\n'
    ret = ret + T + '}\n'
    ret = ret + T + 'std::ifstream in;\n'
    ret = ret + T + 'in.open( argv[1] );\n'
    ret = ret + T + 'std::string prefix( "" );\n'
    ret = ret + T + 'nlohmann::json j;\n'
    ret = ret + T + 'j << in;\n'
    ret = ret + T + 'auto p2 = j.get<{0}>();\n'.format(struct_name)
    ret = ret + T + 'nlohmann::json j2;\n'
    ret = ret + T + 'j2 = p2;\n'
    ret = ret + T + 'std::cout << j2 << std::endl;;\n'
    ## READ IN DATA
    ret = ret + T + 'return 0;\n'
    ret = ret + '}\n'
    return ret





def create_struct_impl(basetypes,structs,struct_name,project):
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

    ret = ret + "void to_json( nlohmann::json& j, const {0}& p ) {{\n\n".format(struct_name)
    ret = ret + T + "j = nlohmann::json{";
    for f in struct_def['FIELDS']:
        ret = ret + '{{"{0}", p.{0}}},\n'.format(f['NAME'])
    ret = ret[:-2]
    ret = ret + '};\n'
    ret = ret + "}\n\n"

    ret = ret + "void from_json( const nlohmann::json& j, {0}& p ) {{\n\n".format(struct_name)
    for f in struct_def['FIELDS']:
        ret = ret + T + 'j.at("{0}").get_to(p.{0});\n'.format(f['NAME'])
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

    ### Defaults
    ret = ret + "void %s::set_defaults( ){\n\n" % (struct_name)
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[ f['TYPE'] ]
                # get default value
                def_val = f['DEFAULT_VALUE']
                # format for complex or not
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
                if len(def_val) == 1:
                    ret = ret + T + 'for (int ii=0; ii<{0}; ii++){{\n'.format(f['LENGTH'])
                    ret = ret + T + T + '{0}[ii] = {1};\n'.format(f['NAME'],def_val[0])
                    ret = ret + T + '}\n'
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
            if 'DEFAULT_VALUE' in f:
                if f['IS_BASETYPE']:
                    b = basetypes[f['TYPE']]
                    # get default value
                    if 'DEFAULT_VALUE' in f:
                        def_val = f['DEFAULT_VALUE']
                    # format for complex or not
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
                if 'VALID_MIN' in f:
                    ret = ret + T + "if ( %s < %s ) {\n" % ( f['NAME'], f['VALID_MIN'] )
                    ret = ret + T + T + 'err_msg +=  "Failed field: %s is less than %s\\n";\n' % ( f['NAME'], f['VALID_MIN'])
                    ret = ret + T + T + 'num_errs++;\n'
                    ret = ret + T + '}\n'
                if 'VALID_MAX' in f:
                    ret = ret + T + "if ( %s > %s ) {\n" % ( f['NAME'], f['VALID_MAX'] )
                    ret = ret + T + T + 'err_msg +=  "Failed field: %s is greater than %s\\n";\n' % ( f['NAME'], f['VALID_MAX'])
                    ret = ret + T + T + 'num_errs++;\n'
                    ret = ret + T + '}\n'
            elif f['IS_STRUCT']:
                ret = ret + T + 'num_errs += %s.validate( err_msg );\n' % ( f['NAME'] )
    ret = ret + T + 'return num_errs;\n';
    ret = ret + "}\n\n"

    return ret
# end create_struct_impl

def create_cmake_file( cpp_src_dir, cpp_inc_dir, basetypes, structs, project ):
    proj_name=project['PROJECT']
    ret = """
cmake_minimum_required(VERSION 2.8)

PROJECT({0})

SET( CMAKE_VERBOSE_MAKEFILE ON )
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

SET( CMAKE_INSTALL_PREFIX "./install" )

SET( AUTOGEN_SRC_DIR  "{1}" )
SET( AUTOGEN_INC_DIR  "{2}" )

# Basic Library
SET( CPP_FILES "{0}_classes.cpp"  )

########### VERBOSE DEBUG ##########
MESSAGE( STATUS "CPP_FILES:" )
FOREACH( loop_var ${{CPP_FILES}} )
    MESSAGE( STATUS "  ${{loop_var}}" )
ENDFOREACH()
########### VERBOSE DEBUG ##########
""".format( proj_name,cpp_src_dir, cpp_inc_dir )

    ret = ret + '\nADD_LIBRARY( {0}_classes ${{CPP_FILES}} )\n\n'.format(proj_name)

    # Sample executables


    for struct_name, struct_def in structs.items():
        ret = ret + 'ADD_EXECUTABLE( print_{0} print_{0}.cpp )\n'.format(struct_name)
        ret = ret + 'TARGET_LINK_LIBRARIES( print_{0} {1}_classes )\n\n'.format(struct_name,proj_name) 

        ret = ret + 'ADD_EXECUTABLE( read_json_{0} read_json_{0}.cpp )\n'.format(struct_name)
        ret = ret + 'TARGET_LINK_LIBRARIES( read_json_{0} {1}_classes )\n\n'.format(struct_name,proj_name) 

        ret = ret + 'ADD_EXECUTABLE( generate_{0} generate_{0}.cpp )\n'.format(struct_name)
        ret = ret + 'TARGET_LINK_LIBRARIES( generate_{0} {1}_classes )\n\n'.format(struct_name,proj_name) 
        




    return ret

# end create_cmake_file


##################################################################################
#
# Main Driver Functions
#
##################################################################################

def generate_CPP( cpp_src_dir, cpp_inc_dir, basetypes, structs, struct_order, project  ):
    if not os.path.exists( cpp_src_dir ):
        os.mkdir(cpp_src_dir)
    if not os.path.exists( cpp_inc_dir ):
        os.mkdir(cpp_inc_dir)

    python_repo_dir = os.path.dirname(os.path.realpath(__file__))

    shutil.copyfile(os.path.join( python_repo_dir, '..',  'support_files', 'json.hpp' ),
                    os.path.join( cpp_inc_dir, 'json.hpp' ) )

    #-----------------------------------------------------
    # Start Headers
    #-----------------------------------------------------
    header_file_name = '{0}_classes.hpp'.format(project['PROJECT'])
    fOut = open( cpp_inc_dir + os.sep + header_file_name, "w" )

    #HEADER Guards
    fOut.write('#ifndef {0}_classes_H\n'.format(project['PROJECT']))
    fOut.write('#define {0}_classes_H\n'.format(project['PROJECT']))
    fOut.write(stock_includes)


    fOut.write( '\n\n' )

    fOut.write('namespace {0} {{\n'.format(project['NAMESPACE']))



    for struct_name in struct_order:
        fOut.write( create_struct_header(basetypes,structs,struct_name,project)) 

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
    fOut.write( '\n\n')
    fOut.write('namespace {0} {{\n'.format(project['NAMESPACE']))


    for struct_name, struct_def in structs.items():
        class_def = create_struct_impl(basetypes, structs, struct_name,project) 
        fOut.write( '\n\n/* ------------------- CLASS {0} -------------------- */\n\n'.format(struct_name))
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

    # printers
    for struct_name, struct_def in structs.items():
        fOut = open( cpp_src_dir + os.sep + "read_json_%s.cpp" % (struct_name), "w" )
        fOut.write( create_json_reader(basetypes,structs,struct_name,project)) 

    # generators
    for struct_name, struct_def in structs.items():
        fOut = open( cpp_src_dir + os.sep + "generate_%s.cpp" % (struct_name), "w" )
        fOut.write( create_struct_generator(basetypes,structs,struct_name,project)) 


    cmake_txt = create_cmake_file( cpp_src_dir, cpp_inc_dir, basetypes, structs, project )
    fOut = open( cpp_src_dir + os.sep + "CMakeLists.txt", "w" )
    fOut.write( cmake_txt )


# end generate_CPP

def get_dependent_structs( structs, struct_name, out ):
    if struct_name in out:
        return out
    struct_def = structs[ struct_name ]
    for field_def in struct_def['FIELDS']:
        if field_def['IS_STRUCT']:
            out = get_dependent_structs(structs,field_def['TYPE'],out)
    out.append(struct_name)
    return out
# end get_dependent_structs
    

def get_struct_order( structs ):
    out = []
    for struct_name, struct_def in structs.items():
        out = get_dependent_structs(structs,struct_name,out)
    return out
# end get_struct_order



if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'inc_dir' )
    parser.add_argument( 'src_dir' )
    parser.add_argument( '--pad', default=8, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    A = AutoGenerator( args.json_basetypes_file, args.json_structures_file,pad=args.pad)
    basetypes = A.basetypes
    structs   = A.structs
    project   = A.project
    struct_order = get_struct_order(structs)
    generate_CPP( args.src_dir, args.inc_dir, basetypes, structs,struct_order,project )
