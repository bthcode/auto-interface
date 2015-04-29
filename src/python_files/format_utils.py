#!/usr/bin/python

import pprint

def calc_running_repeats( arr ):
    start = -1
    summary = {}
    for idx in range(1,len(arr),1):
        v = arr[idx]
        v2 = arr[idx-1]
        if v == v2:
            if start==-1:
                start = idx-1
            summary[ start ] = idx
        else:
            start = -1
            summary[idx] = idx
    return summary
# end cal_running_repeats

def print_list_summary( arr ):
    y = calc_running_repeats(arr)
    out = ''
    for key in sorted(y.keys()):
        start = key; end = y[key]; width = end - start
        if width > 2:
            out = out + '({1}..{2})={0} '.format(arr[start],start,end)
            #print start, "...", end, 
        else:
            for ii in range(start,end+1,1):
                out = out + '{0} '.format(arr[ii])
    return out
# end print_list
    

if __name__=="__main__":
    import numpy as np
    x = np.zeros(1024)
    x[512]=1
    out = print_list_summary(x)
    print out
