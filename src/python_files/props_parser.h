#ifndef PROPS_PARSER_H
#define PROPS_PARSER_H

#include <string>
#include <map>
#include <vector>
#include <sstream>
#include <iostream>

void parse_param_stream( std::istream& r_in_stream, 
                         std::map< std::string, std::string >& r_params );

#endif
