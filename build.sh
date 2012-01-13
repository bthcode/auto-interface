#!/bin/bash

#######################################
#
# Sample Build Script
#
#######################################

echo "Generating Code Based on example.json and basetypes.json"
script_name=`dirname ${0}`
root_dir=`readlink -f $script_name`
c_inc="${root_dir}/src/c_files"
unit_test_dir="${root_dir}/src/unit_test"
python_script=${root_dir}/src/python_files/AutoInterface.py
basetypes=${root_dir}/src/json_files/basetypes.json
out_dir="."


python ${python_script}  ${basetypes}  ${root_dir}/src/json_files/example.json $out_dir

exit

function build_class {
    echo "building $1"
    echo "g++ -fPIC -g ${1}_class_def.cpp -I.  -I${root_dir}/src/c_files/ -c"
    g++ -fPIC -g ${1}_class_def.cpp -I.  -I${c_inc} -c
    echo "g++ -fPIC -g ${1}_mat_support.cpp -c -I. -I${root_dir}/src/c_files/ -I/usr/include/octave-3.4.3/octave/"
    g++ -fPIC -g ${1}_mat_support.cpp -c -I. -I${c_inc} -I/usr/include/octave-3.4.3/octave/
}

function build_mex {
    echo "building mex $1"
    echo "mkoctfile  --mex ${1}_mex_impl.cpp -I. -I${c_inc} -linterface_classes -linterface_mex_support -L."
    mkoctfile  --mex ${1}_mex_impl.cpp -I. -I${c_inc} -linterface_classes -linterface_mex_support -L.

    #echo "mex ${1}_mex_impl.cpp  -I. -I${c_inc} -linterface_classes -linterface_mex_support -L."
    #mex ${1}_mex_impl.cpp  -I. -I${c_inc} -linterface_classes -linterface_mex_support -L.
}
    

echo "Compiling Support"
g++ -fPIC ${root_dir}/src/c_files/props_parser.cpp -I${c_inc}/src/c_files -c

echo "Compiling C Code"
for class in Foo Bar all_types vector_test substruct substruct1 vector_of_structs; do
    build_class $class
done

echo "Creating Shared Libraries..."
g++ --shared *_class_def.o props_parser.o -o libinterface_classes.so
g++ --shared *_mat_support.o -o libinterface_mex_support.so

echo "Compiling Mex..."
for class in Foo Bar all_types vector_test substruct vector_of_structs; do
    build_mex $class
done


mkdir -p unit_test
for t in ${unit_test_dir}/test_*.c; do
    echo "g++ -fPIC -g $t -I. -I${c_inc} -L. -linterface_classes -o unit_test/`basename $t .c`"
    g++ -fPIC -g $t -I. -I${c_inc} -L. -linterface_classes -o unit_test/`basename $t .c`
done


echo 
echo 
echo "Now run tests in unit test"
echo " -- or : octave test/test_Foo.m"
echo " -- or : test/test_all_types"
echo " -- or : octave test/test_all_types.m"
echo " -- or : test/test_vector_test"
echo " -- or : octave test/test_substruct.m"
echo " -- or : test/test_substruct"
echo " -- or : octave test/test_vector_of_structs.m"
echo " -- or : test/test_vector_of_structs"
echo " -- or : octave test/test_vector_test.m"
echo

echo
echo "Make sure you:"
echo "  export LD_LIBRARY_PATH=.:\$LD_LIBRARY_PATH"
echo
echo
