function [ pos, var ] = bufread( pos, buf, type, nelements )
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
        if debug: fprintf('uint8\n'); end
        num_bytes = 1;
    case ('int8')
        if debug: fprintf('int8\n'); end
        num_bytes = 1;
    case ('uint16')
        if debug: fprintf('uint16\n'); end
        num_bytes = 2;
    case ('int16')
        if debug: fprintf('int16\n'); end
        num_bytes = 2;
    case ('uint32')
        if debug: fprintf('uint32\n'); end
        num_bytes = 4;
    case ('int32')
        if debug: fprintf('int32\n'); end
        num_bytes = 4;
    case ('uint64')
        if debug: fprintf('uint64\n'); end
        num_bytes = 8;
    case ('int64')
        if debug: fprintf('int64\n'); end
        num_bytes = 8;
    case ('single')
        if debug: fprintf('single\n'); end
        num_bytes = 4;
    case ('double') 
        if debug: fprintf('double\n'); end
        num_bytes = 8;
    otherwise
        fprintf ('unknown type: %s\n', type);
        return
end

    %% Error Checking
    end_pos = pos + (num_bytes*nelements) -1 ;  % need -1 for inclusive right hand
    if end_pos > length(buf)
        fprintf('Buffer overrun\n');
        return
    end
    %% Type conversion
    var = typecast(buf(pos:end_pos), type);
    pos = pos + num_bytes;

end