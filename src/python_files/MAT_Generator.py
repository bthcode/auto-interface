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

## Function to read vars from a buffer ##

bufread='''function [ pos, var ] = bufread( pos, buf, type, nelements )
% Read a variable from a buffer, as fread() would
%
% USAGE: [ new_position, variable ] = bufread( position, buffer, type, nelements )
%
% Type must be one of 'UINT8', 'INT8', 'UINT16', 'INT16', 'UINT32', 'INT32', 'UINT64',
%    'INT64', 'SINGLE', or 'DOUBLE'
%
% On Error, var will be set to NaN and the original pos will be returned
pos = pos;
var = nan;

debug = 0;

switch lower(type)
    case ('uint8')
        if debug: fprintf('uint8\\n'); end
        num_bytes = 1;
    case ('int8')
        if debug: fprintf('int8\\n'); end
        num_bytes = 1;
    case ('uint16')
        if debug: fprintf('uint16\\n'); end
        num_bytes = 2;
    case ('int16')
        if debug: fprintf('int16\\n'); end
        num_bytes = 2;
    case ('uint32')
        if debug: fprintf('uint32\\n'); end
        num_bytes = 4;
    case ('int32')
        if debug: fprintf('int32\\n'); end
        num_bytes = 4;
    case ('uint64')
        if debug: fprintf('uint64\\n'); end
        num_bytes = 8;
    case ('int64')
        if debug: fprintf('int64\\n'); end
        num_bytes = 8;
    case ('single')
        if debug: fprintf('single\\n'); end
        num_bytes = 4;
    case ('double') 
        if debug: fprintf('double\\n'); end
        num_bytes = 8;
    otherwise
        fprintf ('unknown type: %s\\n', type);
        return
end

    %% Error Checking
    end_pos = pos + (num_bytes*nelements) -1 ;  % need -1 for inclusive right hand
    if end_pos > length(buf)
        fprintf('Buffer overrun\\n');
        return
    end
    %% Type conversion
    var = typecast(buf(pos:end_pos), type);
    pos = pos + (num_bytes*nelements);

end
'''

##################################################################################
#
# MAT STRUCTURE DEFINITIONS AND IMPLEMENTATIONS
#
##################################################################################

def create_set_defaults(basetypes,structs,struct_name):
    ret = 'function [ out ] = set_defaults_{0}()\n'.format( struct_name )
    ret = ret + '%% Create a struct {0}\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: ret = set_defaults_{0}()\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)

    # set defaults
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                basetype = basetypes[f['TYPE']]
                mat_type = basetype['MAT_TYPE']
                # get default value 
                def_val = f['DEFAULT_VALUE']
                # format the default value
                val = '{0}'.format(def_val)
                # set the default value
                ret = ret + T + T + "out.{0} = {1}({2});\n".format(f['NAME'],mat_type,val);
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'out.{0} = set_defaults_{1}();\n'.format(f['NAME'],f['TYPE'])
        # type is basetype, length is vector or int
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            if 'DEFAULT_VALUE' in f:
                if f['IS_BASETYPE']:
                    basetype = basetypes[f['TYPE']]
                    def_val = f['DEFAULT_VALUE']
                    if len(f['DEFAULT_VALUE']) == 1:
                        ret = ret + T + T + 'out.{0} = ones(1,{1})*{2};\n'.format(f['NAME'],f['LENGTH'],def_val[0])
                    else:
                        def_str = ''
                        for idx in range(len(def_val)):
                            def_str = def_str + '{0} '.format(def_val[idx])
                        # set the value
                        ret = ret + T + T + 'out.{0} = [ {1} ];\n'.format(f['NAME'],def_str)
            # type is struct, if vector, if fixed length, fill with defaults
            elif f['IS_STRUCT']:
                # No method for defaulting structs yet, unless they're fixed length
                if type(f['LENGTH']) == int:
                    ret = ret + T + T + 'out.{0} = [ set_defaults_{1}() ];\n'.format( f['NAME'],f['TYPE'] )
                    ret = ret + T + T + 'for ii = 2:{0}\n'.format(f['LENGTH'])
                    ret = ret + T + T + T + 'out.{0}(end+1) = set_defaults_{1}();\n'.format(f['NAME'],f['TYPE'])
                    ret = ret + T + T + 'end\n'
                else:
                    ret = ret + T + T + 'out.{0} = [];\n'.format( f['NAME'] )
            # No default value, just set the element
            else:
                ret = ret + T + T + 'out.{0} = [];\n'.format(f['NAME'])
    ret = ret + 'end\n'

    return ret
# end create_set_defaults

def create_struct_to_struct(basetypes, structs, struct_name):
    '''BTH HERE'''
    ret = 'function [ struct_out ] =  struct_to_struct_{0}(json_struct)\n'.format(struct_name)
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        ret = ret + T + "if isfield(json_struct, '{0}')\n".format(f['NAME'])
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + T + "struct_out.{0} = {1}(json_struct.{0});\n".format(f['NAME'],b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'struct_out.{0} = struct_to_struct_{1}(json_struct.{0});\n'.format(f['NAME'],f['TYPE']) 
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            if f['LENGTH'] == 'VECTOR':
                ret = ret + T + T + "num_elems = length(json_struct.{0});\n".format(f['NAME'])
            else:
                ret = ret + T + T + "num_elems = max({0},length(json_struct.{1}));\n".format(f['LENGTH'],f['NAME'])

            ret = ret + T + T + 'if num_elems > 0\n'
            # now read in that many types
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + T + T + "struct_out.{0} = {1}(json_struct.{0}(1:num_elems));\n".format(f['NAME'], b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                # in the case of a vector of structs, 
                #  we need to declare the vector using the struct 
                #  (hence the if i==1 below)
                ret = ret + T + T + T + 'struct_out.{0} = [];\n'.format(f['NAME'])
                ret = ret + T + T + T + 'for ii=1:num_elems\n'   
                ret = ret + T + T + T + T + 'tmp=struct_to_struct_{0}(json_struct.{1}{{ii}});\n'.format(f['TYPE'],f['NAME'])
                ret = ret + T + T + T + T + 'if ii==1\n'
                ret = ret + T + T + T + T + T + 'struct_out.{0} = [tmp];\n'.format(f['NAME'])
                ret = ret + T + T + T + T + 'else\n'
                ret = ret + T + T + T + T + T + 'struct_out.{0}(end+1)=tmp;\n'.format(f['NAME'])
                ret = ret + T + T + T + T + 'end\n'
                ret = ret + T + T + T + 'end\n'
            ret = ret + T + T + 'else\n' # if num_elems > 0
            ret = ret + T + T + T + 'json_struct.{0} = [];\n'.format(f['NAME'])
            ret = ret + T + T + 'end\n'
        ret = ret + T + 'end % isfield\n\n'
    ret = ret + 'end\n'
    return ret
# end struct_to_struct


def create_read_binary(basetypes,structs,struct_name):
    ret = 'function [ struct_in ] = read_binary_{0}(file_handle)\n'.format(struct_name)
    ret = ret + '%% Read one struct {0} from a binary file handle\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: ret = read_binary_{0}(file_handle)\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + "struct_in.{0} = fread( file_handle, 1, '{1}' );\n".format(f['NAME'],b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                ret = ret + T + 'struct_in.{0} = read_binary_{1}( file_handle );\n'.format(f['NAME'],f['TYPE']) 
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            if f['LENGTH'] == 'VECTOR':
                # get number of elements
                ret = ret + T + "num_elems = fread(file_handle,1,'int32');\n"
            else:
                ret = ret + T + "num_elems = {0};\n".format(f['LENGTH'])
            ret = ret + T + 'if num_elems > 0\n'
            # now read in that many types
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + T + "struct_in.{0} = fread( file_handle, num_elems, '{1}' );\n".format(f['NAME'],b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                # in the case of a vector of structs, 
                #  we need to declare the vector using the struct 
                #  (hence the if i==1 below)
                ret = ret + T + T + 'struct_in.{0} = [];\n'.format(f['NAME'])
                ret = ret + T + T + 'for ii=1:num_elems\n'   
                ret = ret + T + T + T + 'tmp=read_binary_{0}(file_handle);\n'.format(f['TYPE'])
                ret = ret + T + T + T + 'if ii==1\n'
                ret = ret + T + T + T + T + 'struct_in.{0} = [tmp];\n'.format(f['NAME'])
                ret = ret + T + T + T + 'else\n'
                ret = ret + T + T + T + T + 'struct_in.{0}(end+1)=tmp;\n'.format(f['NAME'])
                ret = ret + T + T + T + 'end\n'
                ret = ret + T + T + 'end\n'
            ret = ret + T + 'else\n' # if num_elems > 0
            ret = ret + T + T + 'struct_in.{0} = [];\n'.format(f['NAME'])
            ret = ret + T + 'end\n'
    ret = ret + 'end\n'
    return ret
# end create_read_binary


def create_read_buf(basetypes,structs,struct_name):
    ret = 'function [ pos, struct_out ] = read_buf_{0}( buf, pos )\n'.format(struct_name)
    ret = ret + '%% Read a struct {0} from a buffer\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: [ pos, ret ] = read_buf_{0}()\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)

    struct_def = structs[struct_name]
    # create return struct
    ret = ret + T + 'struct_out = set_defaults_{0}();\n'.format(struct_name)
    for f in struct_def['FIELDS']:
        ret = ret + T + "% -- {0} --\n".format(f['NAME'])
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + "[ pos, struct_out.{0} ] = bufread(pos, buf, '{1}', 1);\n".format(f['NAME'], b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                ret = ret + T + '[ pos, tmp ] = read_buf_{0}( buf, pos );\n'.format(f['TYPE']) 
                ret = ret + T + 'struct_out.{0} = tmp;\n'.format(f['NAME']) 
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            if f['LENGTH'] == 'VECTOR':
                # get number of elements
                ret = ret + T + "[ pos, num_elems ] = bufread(pos, buf 'int32', 1);\n"
            else:
                ret = ret + T + "num_elems = {0};\n".format(f['LENGTH'])
            ret = ret + T + 'if num_elems > 0\n'
            # now read in that many types
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + T + "[ pos, struct_out.{0} ] = bufread( pos, buf, '{1}', num_elems );\n".format(f['NAME'],b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                # in the case of a vector of structs, 
                #  we need to declare the vector using the struct 
                #  (hence the if i==1 below)
                ret = ret + T + T + 'struct_out.{0} = [];\n'.format(f['NAME'])
                ret = ret + T + T + 'for ii=1:num_elems\n'   
                ret = ret + T + T + T + '[pos,tmp]=read_buf_{0}( buf, pos );\n'.format(f['TYPE'])
                ret = ret + T + T + T + 'if ii==1\n'
                ret = ret + T + T + T + T + 'struct_out.{0} = [tmp];\n'.format(f['NAME'])
                ret = ret + T + T + T + 'else\n'
                ret = ret + T + T + T + T + 'struct_out.{0}(end+1)=tmp;\n'.format(f['NAME'])
                ret = ret + T + T + T + 'end\n'
                ret = ret + T + T + 'end\n'
            ret = ret + T + 'else\n' # if num_elems > 0
            ret = ret + T + T + 'struct_out.{0} = [];\n'.format(f['NAME'])
            ret = ret + T + 'end\n'
    ret = ret + 'end\n'
    return ret
# end create_read_buf



def create_write_buf(basetypes,structs,struct_name):
    ret = 'function [ buf ] = write_buf_{0}(struct_out)\n'.format(struct_name)
    ret = ret + '%% Write a struct {0} to a buffer\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: [ buf ] = write_buf_{0}({0}_struct)\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)


    # Empty uint8 buf
    ret = ret + T + "buf = zeros(1,0,'uint8');\n" 
    
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + "buf = [buf typecast({0}(struct_out.{1}),'uint8')];\n".format(b['MAT_TYPE'],f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + "buf = [buf write_buf_{0}(struct_out.{1})];\n".format(f['TYPE'],f['NAME'])
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            if f['LENGTH'] == 'VECTOR':
                # get number of elements
                ret = ret + T + "num_elems=length(struct_out.{0});\n".format(f['NAME'])
                # write number of elements
                ret = ret + T + "buf = [buf typecast(uint32(num_elems),'uint8')];\n".format(f['NAME'])
            else:
                # no need to write number of elements for fixed length, but logic below needs it
                ret = ret + T + "num_elems={0};\n".format(f['LENGTH'])
            ret = ret + T + 'if num_elems > 0\n'
            # now read in that many types
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + T + "buf = [buf typecast({0}(struct_out.{1}),'uint8')];\n".format(b['MAT_TYPE'],f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'for ii=1:num_elems\n'   
                #ret = ret + T + T + T + 'write_binary_{0}(file_handle,struct_out.{1}(ii));\n'.format(f['TYPE'],f['NAME'])
                ret = ret + T + T + T + "buf = [buf write_buf_{0}(struct_out.{1}(ii))];\n".format(f['TYPE'],f['NAME'])
                ret = ret + T + T + 'end\n'
            ret = ret + T + 'end\n' # if num_elems > 0 
    ret = ret + 'end\n'
    return ret
# end create_write_buf


def create_write_binary(basetypes,structs,struct_name):
    ret = 'function [ success ] = write_binary_{0}(file_handle,struct_out)\n'.format(struct_name)
    ret = ret + '%% Write a struct {0} to a binary file\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: [ success ] = write_binary_{0}(file_handle, {0}_struct)\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)


    ret = ret + T + 'success = 0;\n'
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        if ['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + "fwrite(file_handle,struct_out.{0},'{1}');\n".format(f['NAME'],b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                ret = ret + T + 'write_binary_{0}(file_handle,struct_out.{1});\n'.format(f['TYPE'],f['NAME']) 
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            if f['LENGTH'] == 'VECTOR':
                # get number of elements
                ret = ret + T + "num_elems=length(struct_out.{0});\n".format(f['NAME'])
                ret = ret + T + "fwrite(file_handle,num_elems,'int32');\n"
            else:
                ret = ret + T + "num_elems={0};\n".format(f['LENGTH'])
            ret = ret + T + 'if num_elems > 0\n'
            # now read in that many types
            if f['IS_BASETYPE']:
                b = basetypes[f['TYPE']]
                ret = ret + T + T + "fwrite(file_handle,struct_out.{0},'{1}');\n".format(f['NAME'],b['MAT_TYPE'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'for ii=1:num_elems\n'   
                ret = ret + T + T + T + 'write_binary_{0}(file_handle,struct_out.{1}(ii));\n'.format(f['TYPE'],f['NAME'])
                ret = ret + T + T + 'end\n'
            ret = ret + T + 'end\n' # if num_elems > 0 
    ret = ret + 'end\n'
    return ret
# end create_write_binary

def create_write_json(basetypes,structs,struct_name):
    ret = 'function write_json_{0}(fname, struct_out)\n'.format(struct_name)
    ret = ret + '%% Write a struct {0} to a json file\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: [ success ] = write_json_{0}(file_name, {0}_struct)\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)

    ret = ret + T + "savejson('', struct_out, fname);\n"
    ret = ret + 'end\n'
    return ret
# end create_write_json


def create_read_json(basetypes,structs,struct_name):
    ret = 'function [ ret ] =  read_json_{0}(fname)\n'.format(struct_name)
    ret = ret + '%% Read a struct {0} from a json file\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: [ {0}_struct ] = read_json_{0}(file_name)\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)

    ret = ret + T + "tmp = loadjson(fname);\n"
    ret = ret + T + "ret = struct_to_struct_{0}(tmp);\n".format(struct_name)
    ret = ret + 'end\n'
    return ret
# end create_write_json

def create_calc_size(basetypes,structs,struct_name):
    ret = 'function [ struct_size ] = calc_size_{0}(struct_def)\n'.format(struct_name)
    ret = ret + '%% Calculate the binary size of a struct {0}\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% USAGE: [ bytes ] = calc_size_{0}({0}_struct)\n'.format(struct_name)
    ret = ret + '%% \n'
    ret = ret + '%% See also set_defaults_{0}, calc_size_{0}, write_binary_{0}, read_binary_{0}, write_json_{0}, read_json_{0}, read_buf_{0}, write_buf_{0}\n\n'.format(struct_name)

    # If size has been calculated: just return it
    struct_def = structs[struct_name]
    if 'SIZE' not in struct_def or struct_def['SIZE'] == None:
        ret = ret + T + "fprintf('dynamic size calculation not implemented\\n');\n"
        ret = ret + T + "struct_size = 0;\n"
    # Else, calculate it
    else:
        ret = ret + T + 'struct_size = {0};\n'.format(struct_def['SIZE'])
    ret = ret + 'end\n'
    return ret
# end create_calc_size

def create_set_defaults_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "set_defaults_{0}.m".format(struct_name),"w")
        fOut.write(create_set_defaults(basetypes,structs,struct_name))
# end create_set_defaults

def create_read_binary_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "read_binary_{0}.m".format(struct_name),"w")
        fOut.write(create_read_binary(basetypes,structs,struct_name))
# end create_read_binary

def create_write_binary_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "write_binary_{0}.m".format(struct_name),"w")
        fOut.write(create_write_binary(basetypes,structs,struct_name))
# end create_write_binary

def create_calc_sizes_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "calc_size_{0}.m".format(struct_name),"w")
        fOut.write(create_calc_size(basetypes,structs,struct_name))
# end calc_sizes

def create_write_buf_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "write_buf_{0}.m".format(struct_name),"w")
        fOut.write(create_write_buf(basetypes,structs,struct_name))
# end create_write_buf_files

def create_struct_to_struct_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "struct_to_struct_{0}.m".format(struct_name),"w")
        fOut.write(create_struct_to_struct(basetypes,structs,struct_name))
# end create_struct_to_struct

def create_read_buf_files(mat_dir,basetypes,structs):
    # copy read_var utility
    fOut = open(mat_dir + os.sep + 'bufread.m', 'w')
    fOut.write(bufread)
    fOut.close()
    # run struct creator
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "read_buf_{0}.m".format(struct_name),"w")
        fOut.write(create_read_buf(basetypes,structs,struct_name))
# end calc_sizes

def create_write_json_files(mat_dir,basetypes,structs):
    # run struct creator
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "write_json_{0}.m".format(struct_name),"w")
        fOut.write(create_write_json(basetypes,structs,struct_name))
# end calc_sizes

def create_read_json_files(mat_dir,basetypes,structs):
    # run struct creator
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "read_json_{0}.m".format(struct_name),"w")
        fOut.write(create_read_json(basetypes,structs,struct_name))
# end calc_sizes

def generate_mat( mat_dir, basetypes, structs ):
    if not os.path.exists(mat_dir):
        os.mkdir(mat_dir)

    # copy in support files
    python_repo_dir = os.path.dirname(os.path.realpath(__file__))
    jsonlab_dir = python_repo_dir + os.sep + '..' + os.sep + \
                '..' + os.sep + 'submodules' + os.sep + 'jsonlab'

    try:
        shutil.copytree(jsonlab_dir, mat_dir + os.sep + 'jsonlab')
    except:
        print ("jsonlab directory already exists")

    create_set_defaults_files(mat_dir,basetypes,structs)
    create_read_binary_files(mat_dir,basetypes,structs)
    create_write_binary_files(mat_dir,basetypes,structs)
    create_calc_sizes_files(mat_dir,basetypes,structs)
    create_write_buf_files(mat_dir,basetypes,structs)
    create_read_buf_files(mat_dir,basetypes,structs)
    create_write_json_files(mat_dir, basetypes, structs)
    create_read_json_files(mat_dir, basetypes, structs)
    create_struct_to_struct_files(mat_dir, basetypes, structs)
# end generate_mat

if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'mat_dir' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    A = AutoGenerator( args.json_basetypes_file, args.json_structures_file,pad=args.pad)
    basetypes = A.basetypes
    structs   = A.structs
    generate_mat( args.mat_dir, basetypes, structs )
