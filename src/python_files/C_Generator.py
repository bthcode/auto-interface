##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil
from AutoInterface import AutoGenerator

T = '    '



##################################################################################
#
# Utility Functions
#
##################################################################################

funcs_template = '''
int validate_{0}( {0} * p_{0} );
void set_defaults_{0}( {0} * p_{0} );
void write_props_{0}( FILE * r_stream, const char * prefix, int prefix_len, {0} * p_{0} );
void write_binary_{0}( FILE * r_out_stream, {0} * p_{0} );
void read_binary_{0}( FILE * r_in_stream, {0} * p_{0} );
void alloc_{0}( {0} * p_{0} );
void dealloc_{0}( {0} * p_{0} );
'''


##################################################################################
#
# CPP Wrapper for these structs
#
##################################################################################

# create a class that "has_a" struct
# read/write: call c read_binary, c write_binary
# alloc/dealloc: call c alloc, dealloc
# set_defaults / validate: call c
# write props, read props, call c -> maybe update later
def create_cpp_wrapper_for_class( basetypes, structs, struct_name ):
    class_name = "{0}_class".format(struct_name)
    ### Class Def
    ret = ''    
    ret = ret + 'class {0}\n{{\n'.format( class_name )
    ret = ret + T + 'public :\n'
    ret = ret + T + '{0}(){{}};\n'.format(class_name)
    ret = ret + T + '~{0}(){{}};\n'.format(class_name) 
    ret = ret + T + '{0} m_data;\n'.format(struct_name)
    ret = ret + T + 'void set_defaults(){{set_defaults_{0}(&m_data);}};\n'.format(struct_name)
    ret = ret + T + 'void read_binary(FILE * r_in_stream){{read_binary_{0}(r_in_stream,&m_data);}};\n'.format(struct_name)
    ret = ret + T + 'void write_binary(FILE * r_out_stream){{write_binary_{0}(r_out_stream,&m_data);}};\n'.format(struct_name)
    ret = ret + T + 'void write_props(FILE * r_out_stream, const char * prefix, int prefix_len){{write_props_{0}(r_out_stream,prefix,prefix_len,&m_data); }};\n'.format(struct_name)
    ret = ret + '};\n\n\n'
    return ret
# end create_cpp_wrapper_for_class

def create_cpp_wrapper( inc_dir, basetypes, structs, project, struct_order ):
    project_name = project['PROJECT']
    fOut = open( inc_dir + os.sep + '{0}_struct_defs.hpp'.format(project_name), "w" )
    ret = '#ifndef CPP_WRAP_TODO_H\n'
    ret = ret + '#define CPP_WRAP_TODO_H\n'
    ret = ret + '\n#include "{0}_struct_defs.h"\n\n'.format(project_name)
    # now create a wrapper for each struct
    for struct_name in struct_order:
        ret = ret + create_cpp_wrapper_for_class( basetypes, structs, struct_name )
    ret = ret + '#endif // CPP_WRAP_TODO_H\n'
    fOut.write(ret)
# end create_cpp_wrappers



##################################################################################
#
# C STRUCTURE DEFINITIONS AND IMPLEMENTATIONS
#
##################################################################################

def create_c_struct_header( basetypes, structs, struct_name ):
    ''' create a pure c language struct header '''
    struct_def = structs[ struct_name ]
    ret = ''

    ret = ret + "\n\n"

    ### Class Def
    ret = ret + "typedef struct {{\n".format( struct_name )

    ### Member Data
    ret = ret + T + '// Member Fields\n\n'
    for f in struct_def['FIELDS']:
        # Get basic type
        if f['IS_BASETYPE']:
            c_decl = basetypes[ f['TYPE'] ]['C_TYPE']
        elif f['IS_STRUCT']:
            c_decl = '%s' % ( f['TYPE'] )
    
        # Build declaration
        if f['LENGTH'] == 1:
            # nothing to do, decl is already complete
            ret = ret + T + "{0}  {1}; ///<{2}\n".format(c_decl, f['NAME'], f['DESCRIPTION'])
        elif type(f['LENGTH']) == int:
            ret = ret + T + "{0} {1}[{2}]; ///<{3}\n".format(c_decl,f['NAME'],f['LENGTH'],f['DESCRIPTION'])
        elif f['LENGTH'] == 'VECTOR':
            if f['IS_STRUCT']:
                c_decl = '{0} *'.format(f['TYPE'])
            elif f['IS_BASETYPE']:
                c_decl = '{0} *'.format( basetypes[f['TYPE']]['C_TYPE'])
            else:
                print 'ERROR - vector with unknown type or no CONTAINED_TYPE key'
                sys.exit(1)
            ret = ret + T + "{0}  {1}; ///<{2}\n".format( c_decl, f['NAME'], f['DESCRIPTION'] )
            ret = ret + T + "int32_t n_elements_{0};\n".format( f['NAME'] )


    ret = ret + "\n}} {0} ;\n".format( struct_name )

    ret = ret + funcs_template.format(struct_name)

    return ret
# end create_c_struct_header

def create_c_struct_impl( basetypes, structs, struct_name,project ):
    '''Creates the Primary Structure CPP Implementation'''

    struct_def = structs[ struct_name ]

    ret = ''

    ### Allocate
    ret = ret + 'void alloc_{0} ( {0} * p_{0} )\n{{\n'.format(struct_name)
    ret = ret + T + 'p_{0} = ({0} *) malloc( 1 * sizeof({0}) );\n'.format(struct_name)
    ret = ret + '}\n'

    ### De-allocate
    ret = ret + 'void dealloc_{0}( {0} * p_{0} ){{\n'.format(struct_name)
    ret = ret + T + '// Deallocate Allocated Fields\n'
    ret = ret + T + 'int32_t ii;\n'
    #------------------------------------------------------------- 
    # Walk any structs that might have malloc'd data and free it
    #------------------------------------------------------------- 
    for f in struct_def['FIELDS']:
        if f['IS_STRUCT']:
            if f['LENGTH'] == 1:
                ret = ret + T + 'dealloc_{0}( &(p_{1}->{2}) );\n'.format(f['TYPE'],struct_name,f['NAME'])
            elif type(f['LENGTH']) == int:
                ret = ret + T + 'for (ii=0; ii<{0}; ii++ )\n'.format(f['LENGTH'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'dealloc_{0}( &(p_{1}->{2}[ii]) );\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'
            elif f['LENGTH'] == 'VECTOR':
                ret = ret + T + 'for (ii=0; ii<p_{0}->n_elements_{1}; ii++ )\n'.format(struct_name,f['NAME'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'dealloc_{0}( &(p_{1}->{2}[ii]) );\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'
                ret = ret + T + 'if (p_{0}->n_elements_{1} > 0 ){{free( p_{0}->{1} );}}\n'.format(struct_name,f['NAME'])
                ret = ret + T + 'p_{0}->n_elements_{1} = 0;\n'.format(struct_name,f['NAME'])
                ret = ret + T + 'p_{0}->{1} = 0x0;\n'.format(struct_name,f['NAME'])
    ret = ret + "}\n\n"

    ### Read Binary 
    ret = ret + "void read_binary_{0}( FILE * r_stream, {0} * p_{0} ){{\n".format(struct_name)
    ret = ret + T + "int32_t ii;\n"
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + 'read_{0}( r_stream, 1, &(p_{1}->{2}) );\n'.format(f['TYPE'],struct_name,f['NAME']);
            elif f['IS_STRUCT']:
                ret = ret + T + 'read_binary_{0}(r_stream, &(p_{1}->{2}));\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + "\n"
        elif type(f['LENGTH']) == int:
            if f['IS_BASETYPE']:
                ret = ret + T + 'read_{0}( r_stream, {3}, &(p_{1}->{2}[0]) );\n'.format(f['TYPE'],struct_name,f['NAME'],f['LENGTH']);
            elif f['IS_STRUCT']:
                ret = ret + T + 'for (ii=0; ii < {0}; ii++ )\n'.format(f['LENGTH'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'read_binary_{0}(r_stream, &(p_{1}->{2}[ii]));\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'
        elif f['LENGTH'] == 'VECTOR':
            ret = ret + T + "int32_t n_elements_{0};\n".format(f['NAME'])
            ret = ret + T + 'read_INT_32(r_stream,1,&(n_elements_{0}));\n'.format(f['NAME'])
            ret = ret + T + 'p_{0}->n_elements_{1} = n_elements_{1};\n'.format(struct_name,f['NAME'])
            if f['IS_BASETYPE']:
                ctype = basetypes[f['TYPE']]['C_TYPE']
                # ALLOC SPACE
                ret = ret + T + 'if (p_{0}->n_elements_{1} > 0 )'.format(struct_name,f['NAME'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'p_{0}->{1} = ({2}*) malloc(n_elements_{1} * sizeof({2}));\n'.format(struct_name,f['NAME'],ctype);
                ret = ret + T + T + 'read_{0}(r_stream, n_elements_{2}, p_{1}->{2});\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'
                ret = ret + T + 'else\n'
                ret = ret + T + T + 'p_{0}->{1} = 0x0;\n'.format(struct_name,f['NAME'])
                ret = ret + "\n"
            elif f['IS_STRUCT']:
                ctype = f['TYPE']
                # Allocate space for pointers
                ret = ret + T + 'if (p_{0}->n_elements_{1} > 0 )'.format(struct_name,f['NAME'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'p_{0}->{1} = ({2}*) malloc(n_elements_{1} * sizeof({2}));\n'.format(struct_name,f['NAME'],ctype);
                ret = ret + T + '}\n'
                ret = ret + T + 'else\n'
                ret = ret + T + T + 'p_{0}->{1} = 0x0;\n\n'.format(struct_name,f['NAME'])
                ret = ret + T + 'for (ii=0; ii < p_{0}->n_elements_{1}; ii++) {{\n'.format(struct_name,f['NAME'])
                ret = ret + "\n"
                # For each pointer, call read binary
                ret = ret + T + T + 'read_binary_{0}(r_stream, &(p_{1}->{2}[ii]) );\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n\n'
    ret = ret + "}\n\n"

    ### Write Binary 
    ret = ret + "void write_binary_{0}( FILE * r_stream, {0} * p_{0} ){{\n".format(struct_name)
    ret = ret + T + "int32_t ii;\n"
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + 'write_{0}( r_stream, 1, &(p_{1}->{2}) );\n'.format(f['TYPE'],struct_name,f['NAME']);
            elif f['IS_STRUCT']:
                ret = ret + T + 'write_binary_{0}(r_stream, &(p_{1}->{2}));\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + "\n"
        elif type( f['LENGTH'] ) == int:
            if f['IS_BASETYPE']:
                ret = ret + T + 'write_{0}( r_stream, {3}, &(p_{1}->{2}[0]) );\n'.format(f['TYPE'],struct_name,f['NAME'],f['LENGTH']);
            elif f['IS_STRUCT']:
                ret = ret + T + 'for (ii=0; ii < {0}; ii++ )\n'.format(f['LENGTH'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'write_binary_{0}(r_stream, &(p_{1}->{2}[ii]));\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'
                ret = ret + "\n"
        elif f['LENGTH'] == 'VECTOR':
            ret = ret + T + 'write_INT_32(r_stream,1,&(p_{0}->n_elements_{1}));\n'.format(struct_name,f['NAME'])
            if f['IS_BASETYPE']:
                ret = ret + T + 'if (p_{0}->n_elements_{1} > 0 )'.format(struct_name,f['NAME'])
                ret = ret + T + T + 'write_{0}(r_stream,p_{1}->n_elements_{2},p_{1}->{2});\n'.format(f['TYPE'],struct_name,f['NAME']) 
            elif f['IS_STRUCT']:
                ret = ret + T + 'for (ii=0; ii< p_{0}->n_elements_{1}; ++ii )\n'.format(struct_name,f['NAME'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'write_binary_{0}(r_stream, &(p_{1}->{2}[ii]));\n'.format(f['TYPE'], struct_name, f['NAME'])
                ret = ret + T + '}\n\n'
    ret = ret + "}\n\n"

    ### Validate
    ret = ret + 'int validate_{0}( {0} * p_{0} ){{\n'.format( struct_name )
    ret = ret + T + 'printf( "validate not implemented\\n" );\n'
    ret = ret + T + 'return 0;\n'
    ret = ret + '}\n\n'

    ### Set Deafults
    ret = ret + "void set_defaults_{0}( {0} * p_{0} ){{\n".format(struct_name)
    ret = ret + T + "int32_t ii;\n"
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[ f['TYPE'] ]
                # get default value
                def_val = f['DEFAULT_VALUE']
                # format for complex or not
                if b['IS_COMPLEX']:
                    val = '{0} + {1}j'.format(def_val[0],def_val[1])
                else:
                    val = '{0}'.format(def_val)
                # set default value
                ret = ret + T + 'p_{0}->{1} = {2};\n'.format(struct_name,f['NAME'],val)
            elif f['IS_STRUCT']:
                ret = ret + T + 'set_defaults_{0}(&(p_{1}->{2}) );\n'.format( f['TYPE'],struct_name,f['NAME'] )
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
                        ret = ret + T + 'p_{0}->{1}[{2}] = {3} + {4}j;\n'.format(struct_name,
                                                                          f['NAME'],
                                                                          counter,
                                                                          def_val[idx][0],
                                                                          def_val[idx][1])
                        counter = counter+1
                else:
                    num_elements = len(def_val)
                    counter=0
                    for idx in range(len(def_val)):
                        ret = ret + T + 'p_{0}->{1}[{2}] = {3};\n'.format(struct_name,f['NAME'],counter,def_val[idx])
                        counter = counter+1
            elif f['IS_STRUCT']:
                ret = ret + T + 'for (ii=0; ii < {0}; ii++ )\n'.format( f['LENGTH'] )
                ret = ret + T + '{\n'
                ret = ret + T + T + 'set_defaults_{0}( &(p_{1}->{2}[ii]) );\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'

        elif f['LENGTH'] == 'VECTOR':
            print ("WARNING: Setting Default Length for VECTOR Type in C not supported")
            

    ret = ret + "}\n\n"

    ret = ret + "void write_props_{0}( FILE * r_stream, const char * prefix, int prefix_len, {0} * p_{0} )\n".format(struct_name)
    ret = ret + '{\n'
    ret = ret + T + 'char buf[1024];\n'
    ret = ret + T + 'int num_written;\n'
    ret = ret + T + 'int32_t ii=0;\n'
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + 'fprintf( r_stream, "%s", prefix );\n'
                ret = ret + T + 'fprintf( r_stream, "{0} :" );\n'.format(f['NAME'])
                ret = ret + T + 'print_{0}( r_stream, 1, &(p_{1}->{2}) );\n'.format(f['TYPE'],struct_name,f['NAME']);
                ret = ret + T + 'fprintf( r_stream, "\\n" );\n'
            elif f['IS_STRUCT']:
                ret = ret + T + 'num_written = snprintf( buf, 1024, "%s.{0}.", prefix );\n'.format(f['NAME']) 
                ret = ret + T + 'buf[ num_written ] = 0x0;\n'
                ret = ret + T + 'write_props_{0}(r_stream,buf,num_written,&(p_{1}->{2}));\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + "\n"
        elif type( f['LENGTH'] ) == int:
            if f['IS_BASETYPE']:
                ret = ret + T + 'fprintf( r_stream, "%s",  prefix );\n'
                ret = ret + T + 'fprintf( r_stream, "{0} :" );\n'.format(f['NAME'])
                ret = ret + T + 'print_{0}( r_stream, {3}, &(p_{1}->{2}[0]) );\n'.format(f['TYPE'],struct_name,f['NAME'],f['LENGTH']);
                ret = ret + T + 'fprintf( r_stream, "\\n" );\n'
            elif f['IS_STRUCT']:
                ret = ret + T + 'for (ii=0; ii < {0}; ii++ )\n'.format(f['LENGTH'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'num_written = snprintf( buf, 1024, "%s.{0}[ %d ]", prefix, ii );\n'.format(f['NAME']) 
                ret = ret + T + T + 'buf[ num_written ] = 0x0;\n'
                ret = ret + T + T + 'write_props_{0}(r_stream, buf, num_written, &(p_{1}->{2}[ii]));\n'.format(f['TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'
                ret = ret + "\n"
        elif f['LENGTH'] == 'VECTOR':
            if f['IS_BASETYPE']:
                ret = ret + T + 'fprintf( r_stream, "%s",  prefix );\n'
                ret = ret + T + 'fprintf( r_stream, "{0} :" );\n'.format(f['NAME'])
                ret = ret + T + 'print_{0}(r_stream,p_{1}->n_elements_{2},p_{1}->{2});\n'.format(f['TYPE'],struct_name,f['NAME']) 
                ret = ret + T + 'fprintf( r_stream, "\\n" );\n'
            elif f['IS_STRUCT']:
                ret = ret + T + 'fprintf( r_stream, "%s",  prefix );\n'
                ret = ret + T + 'fprintf( r_stream, "{0} :\\n");\n'.format(f['NAME'])
                ret = ret + T + 'for (ii=0; ii< p_{0}->n_elements_{1}; ++ii )\n'.format(struct_name,f['NAME'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'num_written = snprintf( buf, 1024, "%s.{0}[ %d ]", prefix, ii );\n'.format(f['NAME']) 
                ret = ret + T + T + 'buf[ num_written ] = 0x0;\n'
                ret = ret + T + T + 'write_props_{0}(r_stream, prefix, prefix_len,&(p_{1}->{2}[ii]));\n'.format(f['TYPE'], struct_name, f['NAME'])
                ret = ret + T + '}\n\n'

    ret = ret + '}\n\n'


    return ret
# end create_c_struct_impl

def create_default_gen(basetypes,structs,struct_name,project):
    ret = '#include "{0}_struct_defs.h"\n'.format(project['PROJECT'])
    ret = ret + 'int main(int argc, char *argv[])\n'
    ret = ret + '{\n'
    ret = ret + T + 'if (argc != 2 )\n'
    ret = ret + T + '{\n'
    ret = ret + T + T + 'printf( "USAGE: print_{0} <binary>\\n" );\n'.format(struct_name)
    ret = ret + T + T + 'exit(1);\n'
    ret = ret + T + '}\n\n'
    ret = ret + T + 'FILE * fout = fopen( argv[1], "wb" );\n'
    ret = ret + T + '{0} x;\n'.format(struct_name)
    ret = ret + T + 'set_defaults_{0}(&x);\n'.format(struct_name)
    ret = ret + T + 'write_binary_{0}(fout,&x);\n'.format(struct_name)
    ret = ret + T + 'dealloc_{0}(&x);\n'.format(struct_name)
    ret = ret + T + 'fclose(fout);\n\n'
    ret = ret + T + 'return 0;\n'
    ret = ret + '}\n'
    return ret
# end create_printer_for_struct


def create_printer_for_struct(basetypes,structs,struct_name,project):
    ret = '#include "{0}_struct_defs.h"\n'.format(project['PROJECT'])
    ret = ret + 'int main(int argc, char *argv[])\n'
    ret = ret + '{\n'
    ret = ret + T + 'if (argc != 2 )\n'
    ret = ret + T + '{\n'
    ret = ret + T + T + 'printf( "USAGE: print_{0} <binary>\\n" );\n'.format(struct_name)
    ret = ret + T + T + 'exit(1);\n'
    ret = ret + T + '}\n\n'
    ret = ret + T + 'FILE * fin = fopen( argv[1], "rb" );\n'
    ret = ret + T + '{0} x;\n'.format(struct_name)
    ret = ret + T + 'read_binary_{0}(fin,&x);\n'.format(struct_name)
    ret = ret + T + 'write_props_{0}(stdout,"test->",6,&x);\n'.format(struct_name)
    ret = ret + T + 'dealloc_{0}(&x);\n'.format(struct_name)
    ret = ret + T + 'fclose(fin);\n\n'
    ret = ret + T + 'return 0;\n'
    ret = ret + '}\n'
    return ret
# end create_printer_for_struct

    ###############################################################
    # END STRAIGHT C
    ###############################################################

def create_c_headers( inc_dir, basetypes, structs, project_struct):
    '''Creates all structure and matlab support headers'''
    #for struct_name, struct_def in structs.items():
    #    fOut = open( inc_dir + os.sep + "%s_struct_def.h" % (struct_name), "w" )
    #    fOut.write( create_c_struct_header( basetypes, structs, struct_name ) )
    # Now create a master header
    project = project_struct['PROJECT']
    fOut = open( inc_dir + os.sep + '{0}_struct_defs.h'.format(project), "w" ) 
    fOut.write("#ifndef {0}_HEADER_H\n".format(project))
    fOut.write("#define {0}_HEADER_H\n".format(project))
    fOut.write("/**\n")
    fOut.write(" * AutoInterface Generated Code\n" )
    fOut.write(" * \n" )
    fOut.write(" *    PROJECT: {0}\n".format(project))
    fOut.write(" *    VERSION: {0}\n".format(project_struct['VERSION']))
    fOut.write(" */\n\n")

    fOut.write( '// Stock Includes\n')
    fOut.write( '#include <stdlib.h>\n')
    fOut.write( '#include <stdint.h>\n')
    fOut.write( '#include <stdio.h>\n')
    fOut.write( '#include <complex.h>\n')
    fOut.write( '#include <string.h>\n')


    # CPP Guards
    fOut.write('#ifdef __cplusplus\n')
    fOut.write('extern "C" {\n')
    fOut.write('#endif\n')

    for struct_name, struct_def in structs.items():
        fOut.write( create_c_struct_header( basetypes, structs, struct_name ) )
    
    # CPP Guards
    fOut.write('#ifdef __cplusplus\n')
    fOut.write('} // extern "C"\n')
    fOut.write('#endif\n')

    # Header Guard
    fOut.write( "#endif // Header Guard\n".format(project))
    fOut.close()
    
# end create_struct_headers

def create_c_impls( src_dir, basetypes, structs, project):
    '''Creates all structure and matlab support c files'''
    project_name = project['PROJECT']
    fOut = open( src_dir + os.sep + '{0}_struct_defs.c'.format(project_name), "w" ) 
    fOut.write("/**\n")
    fOut.write(" * AutoInterface Generated Code\n" )
    fOut.write(" * \n" )
    fOut.write(" *    PROJECT: {0}\n".format(project_name))
    fOut.write(" *    VERSION: {0}\n".format(project['VERSION']))
    fOut.write(" */\n\n")

    fOut.write( '/* Stock Includes */\n')
    fOut.write( '#include <stdlib.h>\n')
    fOut.write( '#include <stdint.h>\n')
    fOut.write( '#include <stdio.h>\n')
    fOut.write( '#include <complex.h>\n')
    fOut.write( '#include <string.h>\n\n')

    fOut.write( '#include "{0}_struct_defs.h"\n'.format(project_name) )

    for struct_name, struct_def in structs.items():
        c_def = create_c_struct_impl( basetypes, structs, struct_name, project )
        fOut.write( c_def )
    fOut.close()
# end create_struct_impl

def create_printers( src_dir,basetypes,structs,project):
    for struct_name,struct_def in structs.items():
        c_code = create_printer_for_struct(basetypes,structs,struct_name,project)
        fOut = open( src_dir + os.sep + "print_{0}.c".format(struct_name), "w" )
        fOut.write(c_code)
        fOut.close()
# end create_printers

def create_default_generators( src_dir,basetypes,structs,project):
    for struct_name,struct_def in structs.items():
        c_code = create_default_gen(basetypes,structs,struct_name,project)
        fOut = open( src_dir + os.sep + "generate_{0}.c".format( struct_name), "w" )
        fOut.write(c_code)
        fOut.close()
# end create_default_gen


def create_cmake_file( c_src_dir, c_inc_dir, basetypes, structs, project ):
    libname='{0}_structs'.format(project['PROJECT'])
    project_name=project['PROJECT']
    ret = """
cmake_minimum_required(VERSION 2.8)

PROJECT(AutoInterfaceOut)

SET( CMAKE_VERBOSE_MAKEFILE ON )

SET( CMAKE_INSTALL_PREFIX "./install" )

SET( AUTOGEN_SRC_DIR  "{0}" )
SET( AUTOGEN_INC_DIR  "{1}" )

# Basic Library
SET( C_FILES "{2}_struct_defs.c" "io_support.c"  )

########### VERBOSE DEBUG ##########
MESSAGE( STATUS "C_FILES:" )
FOREACH( loop_var ${{C_FILES}} )
    MESSAGE( STATUS "  ${{loop_var}}" )
ENDFOREACH()
########### VERBOSE DEBUG ##########

ADD_LIBRARY( {3} ${{C_FILES}} )

# Sample executables
""".format( c_src_dir, c_inc_dir, project_name, libname )
    for struct_name, struct_def in structs.items():
        ret = ret + 'ADD_EXECUTABLE( print_{0} print_{0}.c )\n'.format(struct_name)
        ret = ret + 'TARGET_LINK_LIBRARIES( print_{0} {1} )\n\n'.format(struct_name, libname) 
        ret = ret + 'ADD_EXECUTABLE( generate_{0} generate_{0}.c )\n'.format(struct_name)
        ret = ret + 'TARGET_LINK_LIBRARIES( generate_{0} {1} )\n\n'.format(struct_name, libname)
    return ret

# end create_cmake_file


def generate_c( src_dir, inc_dir, basetypes, structs, project,struct_order):
    if not os.path.exists(src_dir):
        os.mkdir(src_dir)
    if not os.path.exists(inc_dir):
        os.mkdir(inc_dir)

    # Copy read/write support files
    python_repo_dir = os.path.dirname(os.path.realpath(__file__))
    shutil.copy( python_repo_dir + os.sep + 'io_support.h', 
                 inc_dir + os.sep + 'io_support.h' )
    shutil.copy( python_repo_dir + os.sep + 'io_support.c', 
                 src_dir + os.sep + 'io_support.c' )

    create_c_headers(inc_dir, basetypes, structs,project)
    create_c_impls(src_dir, basetypes, structs,project )
    create_printers(src_dir,basetypes,structs,project)
    create_default_generators(src_dir,basetypes,structs,project)
    # Experimental cpp wrapper
    #create_cpp_wrapper(inc_dir,basetypes,structs,project,struct_order)

    cmake_txt = create_cmake_file( src_dir, inc_dir, basetypes, structs, project )
    fOut = open( src_dir + os.sep + "CMakeLists.txt", "w" )
    fOut.write( cmake_txt )


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'inc_dir' )
    parser.add_argument( 'src_dir' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    A = AutoGenerator(args.json_basetypes_file, args.json_structures_file,pad=args.pad)
    basetypes = A.basetypes
    structs   = A.structs
    project   = A.project
    struct_order = A.struct_order
    generate_c(args.src_dir,args.inc_dir,basetypes,structs,project,struct_order)
