##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil




T="    "

class AutoGenerator:
    """
    Holder class for data associated with auto-interface system.

    members are:
        - basetypes
        - structs

     
    """
    def __init__(self, json_basetypes, json_file, pad=-1 ):
        self.basetypes = json.load( open( json_basetypes,  'r' ) )
        self.project   = json.load( open( json_file, 'r' ) )
        self.pad = pad

        # We want the structures two ways:
        #  - ordered (by occurrence in the json file )
        #  - key/value pair
        structs   = self.project['STRUCTURES']
        self.structs = {}
        self.struct_order = []
        for struct in structs:
            self.struct_order.append( struct['NAME'] )
            self.structs[ struct['NAME'] ] = struct

        if not 'PROJECT' in self.project:
            self.project['PROJECT'] = "Untitled"

        if not 'NAMESPACE' in self.project:
            self.project['NAMESPACE'] = False

        if not 'VERSION' in self.project:
            self.project['VERSION'] = '0.0.1'

        if not 'DESCRIPTION' in self.project:
            self.project['DESCRIPTION'] = ''

        self.preprocess()
    # end __init__

    def preprocess(self):

        # go through keys, send them "to upper"
        any_variable_fields = False
        # go through keys, setting length
        for struct_name, struct_def in self.structs.items():
            # if this struct has any vectors, this will be set to false
            struct_def['IS_VARIABLE_SIZE'] = False
            # track padding and size information
            struct_def['IS_PADDED'] = False
            struct_def['SIZE'] = None
            # inherit the namespace
            if self.project['NAMESPACE']:
                struct_def['NAMESPACE'] = self.project['NAMESPACE']
            for idx, f in enumerate(struct_def['FIELDS']):
                # move keys to upperclass
                for key,val in f.items():
                    #f[key.upper()] = val
                    #mydict[new_key] = mydict.pop(old_key)
                    f[key.upper()] = f.pop(key)

                # SET LENGTH 
                if not 'LENGTH' in f:
                    f['LENGTH'] = 1
                elif f['LENGTH'] == 'VECTOR':
                    struct_def['IS_VARIABLE_SIZE'] = True
                    any_variable_fields = True
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
                if not 'DESCRIPTION' in f:
                    f['DESCRIPTION'] = ''

                # Doc name
                if f['IS_BASETYPE']:
                    f['DOC_NAME'] = self.basetypes[f['TYPE']]['DOC_NAME']
                else:
                    f['DOC_NAME'] = f['TYPE']
                

                # Handle default value setting
                if f['IS_BASETYPE'] and f['LENGTH'] == 1:
                    if not 'DEFAULT_VALUE' in f:
                        f['DEFAULT_VALUE'] = self.basetypes[f['TYPE']]['DEFAULT_VALUE'] 
                elif f['IS_BASETYPE'] and type(f['LENGTH']) == int:
                    # no value
                    if not 'DEFAULT_VALUE' in f:
                        f['DEFAULT_VALUE'] = [ self.basetypes[f['TYPE']]['DEFAULT_VALUE'] ] * f['LENGTH']
                    # one value: repeat it
                    elif len(f['DEFAULT_VALUE']) == 1:
                        f['DEFAULT_VALUE'] = [ f['DEFAULT_VALUE'] ] * f['LENGTH']
                    # only other ok value is default value is correct length
                    elif len(f['DEFAULT_VALUE']) != f['LENGTH']:
                        print ("Bad Default for {0}: {1}".format(f['NAME'], f['DEFAULT_VALUE']))
                struct_def[idx] = f
                # set missing types
                # handle default values
            if not 'DESCRIPTION' in struct_def:
                struct_def['DESCRIPTION'] = ''
            self.structs[struct_name] = struct_def
        # turn dicts into classes

        for base_name, basetype in self.basetypes.items():
            if not 'IS_COMPLEX' in basetype:
                basetype['IS_COMPLEX'] = False
            else:
                if basetype['IS_COMPLEX'].upper() == "TRUE":
                    basetype['IS_COMPLEX'] = True
                else:
                    basetype['IS_COMPLEX'] = False

            # Set CPP_TYPE and STREAM_TIME fields
            if not 'CPP_TYPE' in basetype:
                basetype['CPP_TYPE'] = basetype['C_TYPE']
            if not 'STREAM_CAST' in basetype:
                basetype['STREAM_CAST'] = basetype['CPP_TYPE']
            self.basetypes[base_name]=basetype

        if self.pad > 0:
            if any_variable_fields:
                print ("Found variable length fields, padding impossible")
                sys.exit(1)
            else:
                print ("padding to {0}".format(self.pad))
            for struct_name in self.structs.keys():
                if self.structs[struct_name]['IS_PADDED'] == False:
                    self.insert_padding( struct_name, self.structs, pad_to=self.pad )
        else:
            print ("no padding")
    # end preprocess

    def insert_padding(self,struct_name,structs,pad_to=8):
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
        sum_bytes=0
        pad_counter=0;
        out_fields = []
        largest_alignment = 1
        for idx, f in enumerate(struct_def['FIELDS']):
            if type(f['LENGTH']) == int:
                if f['IS_BASETYPE']:
                    b = self.basetypes[f['TYPE']]
                    field_bytes = b['LENGTH']
                elif f['IS_STRUCT']:
                    if not self.structs[f['TYPE']]['IS_PADDED']:
                        self.insert_padding( f['TYPE'], self.structs, pad_to=self.pad )
                    field_bytes = self.structs[f['TYPE']]['SIZE']
                # fields should be aligned according to their length, but 
                #  not larger than the target word size
                target_pad = min( pad_to, field_bytes )
                largest_alignment = max( target_pad, largest_alignment )
                #print ('{0}, {1}'.format(f['NAME'], sum_bytes))
                if sum_bytes % target_pad != 0:
                    #import ipdb; ipdb.set_trace()
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
                    #print ( "Inserting pad, length {1} before {0}".format(f['NAME'],pad_length) )  
            elif f['LENGTH'] == 'VECTOR':
                print( "WARNING! Cannot pre-pad structs with variable length" )
                sys.exit(1)
            sum_bytes += field_bytes * f['LENGTH']
            #print ( "end of {0}, sum_bytes = {1}".format( f['NAME'], sum_bytes ) )
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
            #print ( "Inserting pad, length {1} before {0}".format(f['NAME'],pad_length) )  

        #TODO : do we pad the end of the struct?
        self.structs[struct_name]['FIELDS'] = out_fields
        self.structs[struct_name]['IS_PADDED'] = True
        self.structs[struct_name]['SIZE']    = sum_bytes
                
    # end insert_padding

# end class AutoGenerator



if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser('')
    parser.add_argument( 'basetypes' )
    parser.add_argument( 'json_file' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    parser.set_defaults(pad=-1)
    args = parser.parse_args()
    print (pprint.pformat(args))
    A = AutoGenerator(args.basetypes, args.json_file, pad = args.pad) 
    import pprint
    print (pprint.pformat(A.basetypes))
    print (pprint.pformat(A.structs))
    print (pprint.pformat(A.struct_order))
