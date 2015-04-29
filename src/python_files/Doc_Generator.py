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


def create_rst( basetypes, structs, struct_name ):
    heading = "*" * len( struct_name )
    ret = "{0}\n{1}\n{0}\n\n".format(heading,struct_name,heading)

    struct_def = structs[struct_name]

    if struct_def.has_key( 'DESCRIPTION' ):
        ret = ret + struct_def[ 'DESCRIPTION' ] + "\n\n"

    # these are required to calculate the field width 
    #   when making the table
    fields_header = 'Fields'
    fields_length = len(fields_header)
    types_header = 'Types'
    types_length = len(types_header)
    lengths_header = 'Length(Bytes)'
    lengths_length = len(lengths_header)
    descriptions_header='Description'
    descriptions_length = len(descriptions_header)
    defaults_header='Defaults'
    defaults_length = len(defaults_header)

    fields = []
    types = []
    lengths = []
    descriptions = []
    defaults = []

    for f in struct_def['FIELDS']:
        fields.append(f['NAME'])
        fields_length = max(len(fields[-1]),fields_length)
        types.append(f['TYPE'])
        types_length = max(len(types[-1]),types_length)
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                lengths.append(str(basetypes[f['TYPE']]['LENGTH']))
            else:
                lengths.append('STRUCTURE')
        elif f['IS_BASETYPE'] and type(f['LENGTH']) == int:
            length = f['LENGTH']
            width  = int(basetypes[f['TYPE']]['LENGTH'])
            total  = length * width
            lengths.append('{0} * {1} = {2}'.format( length,width,total ) )
                                                    
        else:
            lengths.append('VARIABLE')
        lengths_length = max(len(lengths[-1]),lengths_length)
        descriptions.append(str(f['DESCRIPTION']))
        descriptions_length = max(len(descriptions[-1]),descriptions_length)
        if f['IS_BASETYPE'] and f['LENGTH']!='VECTOR':
            if f['LENGTH'] == 1:
                defaults.append(str(f['DEFAULT_VALUE']))
            else:
                defaults.append(format_utils.print_list_summary(f['DEFAULT_VALUE']))
        else:
            defaults.append('')
        defaults_length = max(len(defaults[-1]),defaults_length)

    print fields
    print types
    print lengths
    print descriptions
    print defaults

    magic_row = "="*fields_length + " " + \
                "="*types_length + " " + \
                "="*lengths_length + " " + \
                "="*descriptions_length + " " + \
                "="*defaults_length + "\n"
    print magic_row
    ret = ret + magic_row
    ret = ret + fields_header.ljust(fields_length) + " " + \
                types_header.ljust(types_length) + " " + \
                lengths_header.ljust(lengths_length) + " " + \
                descriptions_header.ljust(descriptions_length) + " " + \
                defaults_header + "\n"
    ret = ret + magic_row

    for idx, field in enumerate(fields):
        ret = ret + fields[idx].ljust(fields_length) + " " + \
                    types[idx].ljust(types_length) + " " + \
                    lengths[idx].ljust(lengths_length) + " " + \
                    descriptions[idx].ljust(descriptions_length) + " " + \
                    defaults[idx].ljust(defaults_length) + "\n"

    ret = ret + magic_row + "\n\n"

    print ret
        
    return ret
# end generate_rst


def generate_docs( project_name, project_version, project_description, doc_dir, basetypes, struct_order, structs, overwrite=True ):
    if overwrite:
        if os.path.exists( doc_dir ):
            shutil.rmtree( doc_dir )

        python_repo_dir = os.path.dirname(os.path.realpath(__file__))
        shutil.copytree( python_repo_dir + os.sep + 'sphinx_in', 
                     doc_dir  )

    fOut = open( doc_dir + os.sep + 'generated.rst', 'w' )
    generated = '''
###########################
Project: {0}
###########################

Version: {1}
Description: {2}

====================
Generated Structures 
====================

'''.format( project_name, project_version, project_description )
    for struct_name in struct_order: 
        generated = generated + create_rst( basetypes, structs, struct_name )
    fOut.write( generated )
    fOut.close()
# end create_py_files


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'output_directory' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    json_basetypes = args.json_basetypes_file
    json_file = args.json_structures_file
    out_dir = args.output_directory
    A = AutoGenerator( json_basetypes, json_file,pad=args.pad )
    basetypes = A.basetypes
    structs   = A.structs
    pname = A.project['PROJECT']
    pdesc = A.project['DESCRIPTION']
    pver  = A.project['VERSION']
    struct_order = A.struct_order

    generate_docs( pname, pdesc, pver, out_dir, basetypes, struct_order, structs, overwrite=True )
