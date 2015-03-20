#include "props_parser.h"

void parse_param_stream( std::istream& r_in_stream, 
                         std::map< std::string, std::string>& r_params )
{
    std::string line;
    while ( std::getline( r_in_stream, line ) )
    {
        //std::cout << "line pre = |" << line << "|" <<  std::endl;

        // 1. find and strip from the first comment on
        std::size_t ii;
        ii = line.find( "#" );
        if ( ii != line.npos )
        {
            line.erase( ii );
        }

        // 2. rstrip
        ii = line.find_last_not_of( " \\t\\n\\r" );
        if ( ii != line.npos )
        {
            line.erase( ii+1 );
        }

        // 3. lstrip
        ii = line.find_first_not_of( " \\t\\n\\r" );
        if ( ii != line.npos )
        {
            line.erase( 0, ii );
        }

        // 3. anything left on the line?
        if ( 0 == line.size() )
        {
            continue;
        }

        //std::cout << "line post = |" << line << "|" <<  std::endl;

        // 4. Find the = 
        ii = line.find( "=" );
        if ( ii != line.npos )
        {       
            std::string key = line.substr( 0,ii );
            std::string val = line.substr( ii+1, line.npos );


            ii = key.find_last_not_of( " \\t\\n\\r" );
            //std::cout << "key pre = |" << key << "|" << std::endl;
            if ( ii != key.npos )
            {
                key.erase( ii+1 );
            }
            //std::cout << "key post = |" << key << "|" << std::endl;


            //std::cout << "val pre = |" << val << "|" << std::endl;
            ii = val.find_first_not_of( " \\t\\n\\r" );
            if ( ii != val.npos )
            {
                val.erase( 0, ii );
            }
            //std::cout << "val post = |" << val << "|" << std::endl;
            r_params.insert( std::make_pair( key, val ) );
        }
    }
}
