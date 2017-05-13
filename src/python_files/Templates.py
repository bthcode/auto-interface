#!/usr/bin/python

__author__="Brian Hone"

'''
Place to store templates for AutoInteface system
'''

py_class_template = '''
class {0}(object):
    """
    Auto Generated Class {0}
    Methods:
      __init__ : Sets defaults
      read_binary( file_handle )
      write_binary( file_handle )
    """
'''

py_basic_methods = '''
    def __init__(self):
        self.set_defaults() 
    # end __init__

    
    def read_props(self):
        pass
    # end write_props

    def validate(self):
        pass
    # end validate

    def __repr__(self):
        ret = ''
        for field in self.__slots__:
            val = getattr(self, field)
            #for key, val in sorted(vars(self).items()):
            ret = ret + "{0}: {1}\\n".format( field, val )
        return ret
     # end __repr__

    def set_defaults(self):
'''

ctypes_class_template = '''
class {0}(ctypes.Structure):
    """
    Auto Generated Class {0}
    Methods:
      __init__ : Sets defaults
      read_binary( file_handle )
      write_binary( file_handle )
    """
'''

ctypes_basic_methods = '''
    def __init__(self):
        pass 
    # end __init__

    def pretty_print(self):
        formatter = Formatter()
        d = to_ordered_dict(self) 
        return formatter(d)
    # end pretty_print

    def to_dict(self):
        return todict(self)
    # end to_dict

    def __repr__(self):
        return pprint.pformat(self.to_dict())
    # end __repr__

    # from dict
    def from_dict(self,d):
        """
        .. function:: from_dict()
        Populate this object from a dict
        :param d
           dict source
       :rtype None
        """
        fromdict(self,d)
    # end from_dict



    # read json
    def to_json(self):
        """
        .. function:: to_json()
           JSONify this object
           :param None'
           :rtype string
        """
        d = todict(self)
        return json.dumps(d)
    # end to_json

    # read json
    def from_json( self, r_stream ):
        """
    .. function:: from_json()
       read JSON into this object
       :param file handle'
       :rtype None
        """
        json_obj = json.loads(r_stream.read())
        self.from_dict(json_obj)
    # end from_json

    # read binary
    def read_binary( self, r_stream ):
        """
    .. function:: read_binary( file_handle )
       Read this class from a packed binary message
       :param r_stream an open filehandle (opened in mode rb )
       :rtype None
        """
        r_stream.readinto(self)
    # end read_binary


    # write binary
    def write_binary( self, r_stream, typecheck=False ):
        """
    .. function:: read_binary( file_handle )
       Write this class to a packed binary message
       :param r_stream an open filehandle (opened in mode wb )
       :typecheck if True, verify structures are correct type before including in arrays
       :rtype None
        """
        r_stream.write(self)
    # end write_binary


    def set_defaults(self):
'''

