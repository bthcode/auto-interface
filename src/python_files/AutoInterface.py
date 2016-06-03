##############################################################################
#
# Code Generator System
#
##############################################################################
import json
import string
import pprint
import sys
import os
import shutil


__author__ = "Brian Hone"


class AutoGenerator:
    """
    Holder class for data associated with auto-interface system.

    This class does all the pre-processing required by the various generators.

    members are:
        - basetypes
        - structs

    each basetype has:
        - c_type
        - default_value
        - mex_type
        - mat_type
        - GPB_type - google protocol buffers
        - length - bytes
        - doc_name - for printing documents

    each project has:
        - project
        - version
        - namespace
        - description
        - structures - list of structures

    each structure has:
        - name
        - description
        - fields - list of fields

    each field has:
        - name
        - type  - must exist in basetypes
        - description
        - default_value
        - valid_min
        - valid_max
        - length - 1 = scalar, >1 = fixed array, or VARIABLE
    """
    def __init__(self, json_basetypes, json_file, pad=-1):
        self.basetypes = json.load(open(json_basetypes,  'r'))
        self.project = json.load(open(json_file, 'r'))
        self.pad = pad

        # We want the structures two ways:
        #  - ordered (by occurrence in the json file )
        #  - key/value pair
        structs = self.project['STRUCTURES']
        self.structs = {}
        self.struct_order = []
        for struct in structs:
            self.struct_order.append(struct['NAME'])
            self.structs[struct['NAME']] = struct

        if 'PROJECT' not in self.project:
            self.project['PROJECT'] = "Untitled"

        if 'NAMESPACE' not in self.project:
            self.project['NAMESPACE'] = False

        if 'VERSION' not in self.project:
            self.project['VERSION'] = '0.0.1'

        if 'DESCRIPTION' not in self.project:
            self.project['DESCRIPTION'] = ''

        self.preprocess()
    # end __init__

    def preprocess(self):
        '''
        - Determine if there are any variable length fields
        - Set structure defaults
            - size, length, namespace, is_basetype, is_struct, is_complex,
              cpp_type, c_type, stream_type
        - Make all structure keys upper()
        - Recursively insert padding if padding is specified
        '''

        # go through keys, send them "to upper"
        any_variable_fields = False
        # go through keys, setting length
        for struct_name, struct_def in self.structs.items():
            # if this struct has any vectors, this will be set to false
            struct_def['IS_VARIABLE_SIZE'] = False
            # track padding and size information
            struct_def['IS_PADDED'] = False
            struct_def['IS_VARIABLE_SIZE_TESTED'] = False
            struct_def['SIZE'] = None
            # inherit the namespace
            if self.project['NAMESPACE']:
                struct_def['NAMESPACE'] = self.project['NAMESPACE']
            for idx, f in enumerate(struct_def['FIELDS']):
                # move keys to upperclass
                for key, val in f.items():
                    f[key.upper()] = f.pop(key)

                # SET LENGTH
                if 'LENGTH' not in f:
                    f['LENGTH'] = 1
                elif f['LENGTH'] == 'VECTOR':
                    any_variable_fields = True
                    pass
                else:
                    try:
                        f['LENGTH'] = int(f['LENGTH'])
                    except:
                        f['LENGTH'] = 1
                        print ("ERROR: Bad length for field {0}".format(f['NAME']))
                        sys.exit(1)

                # Determine if is struct
                if f['TYPE'] in self.structs:
                    f['IS_STRUCT'] = True
                    f['IS_BASETYPE'] = False
                elif f['TYPE'] in self.basetypes:
                    f['IS_STRUCT'] = False
                    f['IS_BASETYPE'] = True
                else:
                    print ("ERROR: Unknown Type: {0}".format(f['TYPE']))
                if 'DESCRIPTION' not in f:
                    f['DESCRIPTION'] = ''

                # Doc name
                if f['IS_BASETYPE']:
                    f['DOC_NAME'] = self.basetypes[f['TYPE']]['DOC_NAME']
                else:
                    f['DOC_NAME'] = f['TYPE']

                # Handle default value setting
                if f['IS_BASETYPE'] and f['LENGTH'] == 1:
                    if 'DEFAULT_VALUE' not in f:
                        f['DEFAULT_VALUE'] = self.basetypes[f['TYPE']]['DEFAULT_VALUE']
                elif f['IS_BASETYPE'] and type(f['LENGTH']) == int:
                    # no value
                    if 'DEFAULT_VALUE' not in f:
                        f['DEFAULT_VALUE'] = [self.basetypes[f['TYPE']]['DEFAULT_VALUE']] * f['LENGTH']
                    # one value: repeat it
                    elif len(f['DEFAULT_VALUE']) == 1:
                        f['DEFAULT_VALUE'] = [f['DEFAULT_VALUE']] * f['LENGTH']
                    # only other ok value is default value is correct length
                    elif len(f['DEFAULT_VALUE']) != f['LENGTH']:
                        print ("Bad Default for {0}: {1}".format(f['NAME'], f['DEFAULT_VALUE']))
                struct_def[idx] = f
                # set missing types
                # handle default values
            if 'DESCRIPTION' not in struct_def:
                struct_def['DESCRIPTION'] = ''
            self.structs[struct_name] = struct_def

        for base_name, basetype in self.basetypes.items():
            if 'IS_COMPLEX' not in basetype:
                basetype['IS_COMPLEX'] = False
            else:
                if basetype['IS_COMPLEX'].upper() == "TRUE":
                    basetype['IS_COMPLEX'] = True
                else:
                    basetype['IS_COMPLEX'] = False

            # Set CPP_TYPE and STREAM_TIME fields
            if 'CPP_TYPE' not in basetype:
                basetype['CPP_TYPE'] = basetype['C_TYPE']
            if 'STREAM_CAST' not in basetype:
                basetype['STREAM_CAST'] = basetype['CPP_TYPE']
            self.basetypes[base_name] = basetype

        # find variable fields
        # any_variable_fields = self.find_variable_fields(struct_name)
        for struct_name in self.structs.keys():
            if self.structs[struct_name]['IS_VARIABLE_SIZE_TESTED'] is False:
                if self.find_variable_fields(struct_name):
                    any_variable_field = True

        # if there are variable fields, structs can only be padded to
        #  1 byte sizes
        if self.pad > 0:
            if self.pad > 1 and any_variable_fields:
                print ("Found variable length fields, padding impossible")
                sys.exit(1)
            else:
                print ("padding to {0}".format(self.pad))
            for struct_name in self.structs.keys():
                if self.structs[struct_name]['IS_PADDED'] is False:
                    # Note that insert padding also calculates structure size
                    self.insert_padding(struct_name, self.structs, pad_to=self.pad)
        else:
            print ("no padding")
    # end preprocess

    def find_variable_fields(self, struct_name):
        ''' finds all the variable sized structs - note: recursive
            -- use this info later when trying to pad the structures and calc their size '''
        struct_def = self.structs[struct_name]
        if self.structs[struct_name]['IS_VARIABLE_SIZE_TESTED']:
            return self.structs[struct_name]['IS_VARIABLE_SIZE']
        for idx, f in enumerate(struct_def['FIELDS']):
            if f['LENGTH'] == 'VECTOR':
                self.structs[struct_name]['IS_VARIABLE_SIZE'] = True
            if f['IS_STRUCT']:
                substruct_name = f['TYPE']
                if not self.structs[substruct_name]['IS_VARIABLE_SIZE_TESTED']:
                    self.find_variable_fields(substruct_name)
                if self.structs[substruct_name]['IS_VARIABLE_SIZE']:
                    self.structs[struct_name]['IS_VARIABLE_SIZE'] = True
        self.structs[struct_name]['IS_VARIABLE_SIZE_TESTED'] = True
        return self.structs[struct_name]['IS_VARIABLE_SIZE']
    # end find variable sizing

    def insert_padding(self, struct_name, structs, pad_to=8):
        ''' Inserts padding using the following rules:
            1. pad basic type to width of that type
            2. pad end of struct to widest alignment in that struct '''
        pad_template = {'DEFAULT_VALUE': 0,
                        'DESCRIPTION': '',
                        'IS_BASETYPE': True,
                        'IS_STRUCT': False,
                        'LENGTH': 1,
                        'NAME': 'pad',
                        'TYPE': 'UINT_8'}
        struct_def = self.structs[struct_name]
        # We can't pad a variable sized structure, so don't try
        if struct_def['IS_VARIABLE_SIZE']:
            self.structs[struct_name]['SIZE'] = 'VARIABLE'
            self.structs[struct_name]['IS_PADDED'] = True
            return
        sum_bytes = 0
        pad_counter = 0
        out_fields = []
        largest_alignment = 1
        for idx, f in enumerate(struct_def['FIELDS']):
            if type(f['LENGTH']) == int:
                if f['IS_BASETYPE']:
                    b = self.basetypes[f['TYPE']]
                    field_bytes = b['LENGTH']
                elif f['IS_STRUCT']:
                    if not self.structs[f['TYPE']]['IS_PADDED']:
                        self.insert_padding(f['TYPE'], self.structs, pad_to=self.pad)
                    field_bytes = self.structs[f['TYPE']]['SIZE']
                # fields should be aligned according to their length, but
                #  not larger than the target word size
                target_pad = min(pad_to, field_bytes)
                largest_alignment = max(target_pad, largest_alignment)
                if sum_bytes % target_pad != 0:
                    pad_name = "pad_{0}".format(pad_counter)
                    pad_counter += 1
                    pad_length = target_pad - sum_bytes % target_pad
                    field = {}
                    field['NAME'] = pad_name
                    field['LENGTH'] = pad_length
                    field['IS_BASETYPE'] = True
                    field['IS_STRUCT'] = False
                    field['TYPE'] = 'UINT_8'
                    field['DOC_NAME'] = 'u8'
                    if pad_length == 1:
                        field['DEFAULT_VALUE'] = 170
                    else:
                        field['DEFAULT_VALUE'] = [170] * pad_length
                    field['DESCRIPTION'] = 'PADDING FOR ALIGNMENT'
                    out_fields.append(field)
                    sum_bytes += target_pad - sum_bytes % target_pad
            elif f['LENGTH'] == 'VECTOR':
                print("WARNING! Cannot pre-pad structs with variable length")
                sys.exit(1)
            sum_bytes += field_bytes * f['LENGTH']
            out_fields.append(f)
        if sum_bytes % largest_alignment != 0:
            target_pad = largest_alignment
            pad_name = "pad_{0}".format(pad_counter)
            pad_counter += 1
            pad_length = target_pad - sum_bytes % target_pad
            field = {}
            field['NAME'] = pad_name
            field['LENGTH'] = pad_length
            field['IS_BASETYPE'] = True
            field['IS_STRUCT'] = False
            field['TYPE'] = 'UINT_8'
            field['DOC_NAME'] = 'u8'
            field['DEFAULT_VALUE'] = [170] * pad_length
            field['DESCRIPTION'] = 'PADDING FOR ALIGNMENT'
            out_fields.append(field)
            sum_bytes += target_pad - sum_bytes % target_pad

        # TODO : do we pad the end of the struct
        self.structs[struct_name]['FIELDS'] = out_fields
        self.structs[struct_name]['IS_PADDED'] = True
        self.structs[struct_name]['SIZE'] = sum_bytes
    # end insert_padding
# end class AutoGenerator

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser('')
    parser.add_argument('basetypes')
    parser.add_argument('json_file')
    parser.add_argument('--pad',
                        default=-1,
                        type=int,
                        help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    parser.set_defaults(pad=-1)
    args = parser.parse_args()
    print (pprint.pformat(args))
    A = AutoGenerator(args.basetypes, args.json_file, pad=args.pad)
    import pprint
    print (pprint.pformat(A.basetypes))
    print (pprint.pformat(A.structs))
    print (pprint.pformat(A.struct_order))
