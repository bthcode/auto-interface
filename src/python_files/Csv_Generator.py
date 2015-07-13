#!/usr/bin/env python

__author__="Brian Hone"

'''
Code Generator

Generates AutoInterface documentation
'''

import json, string, pprint, sys, os
import shutil
from AutoInterface import AutoGenerator
from Templates import py_class_template
import format_utils

T="    "


def create_csv( basetypes, structs, struct_name ):
    
    ret = "\n\nName,{0}\n".format(struct_name)

    struct_def = structs[struct_name]

    if struct_def.has_key( 'DESCRIPTION' ):
        ret = ret + "Description,{0}\n\n".format(struct_def['DESCRIPTION'])

    # Header line
    ret = ret + "Field Name, Data Type, Units, Length, Description\n"
    
    # Fields
    for f in struct_def['FIELDS']:
        name       = f['NAME']
        field_type = f['DOC_NAME']
        length     = f['LENGTH']
        descr      = f['DESCRIPTION']

        # note: units is empty
        ret = ret + "{0}, {1}, , {2}, {3}\n".format(name,field_type,length,descr)

         

        
    return ret
# end generate_rst


def generate_docs( project_name, project_version, project_description, output_file, basetypes, struct_order, structs, overwrite=True ):

    fOut = open( output_file, 'w' )
    generated = '''
Project, {0}
Version, {1}
Description, {2}

'''.format( project_name, project_version, project_description )
    for struct_name in struct_order: 
        generated = generated + create_csv( basetypes, structs, struct_name )
    fOut.write( generated )
    fOut.close()
# end create_py_files


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'output_file' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    json_basetypes = args.json_basetypes_file
    json_file = args.json_structures_file
    output_file = args.output_file 
    A = AutoGenerator( json_basetypes, json_file,pad=args.pad )
    basetypes = A.basetypes
    structs   = A.structs
    pname = A.project['PROJECT']
    pdesc = A.project['DESCRIPTION']
    pver  = A.project['VERSION']
    struct_order = A.struct_order

    generate_docs( pname, pdesc, pver, output_file, basetypes, struct_order, structs, overwrite=True )
