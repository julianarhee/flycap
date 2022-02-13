#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   preprocess_movies.py
@Time    :   2022/02/12 18:28:49
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''

import os
import glob
import sys
import re
import json
import optparse
import traceback
import pprint

pp = pprint.PrettyPrinter(indent=4)
from crop_movies import do_crop
from concatenate_movies import concatenate_subvideos, cleanup_dir


natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]

def get_param_filepaths(session=None, rootdir='/mnt/sda/Videos'):
    '''
    Finds all SESSION_preprocessing.json files in assay dirs.
    Files are created by crop_params.py
    '''
    
    session_str = '20*' if session is None else session
    found_files = sorted(glob.glob(os.path.join(rootdir, '*', '%s_preprocessing.json' % session_str)), 
                         key=natsort)
                         
    print('Found %i sessions to process:' % len(found_files))
    for f in found_files:
        print('    %s' % f)
        
    return found_files

if __name__ == '__main__':

    
    parser = optparse.OptionParser()
    parser.add_option('--rootdir', action="store", 
                      dest="rootdir", default='/mnt/sda/Videos', 
                      help="out path directory [default: /mnt/sda/Videos]")
    parser.add_option('--session', action="store", 
                      dest="session", default=None, 
                      help="YYYYMMDD [default: None, processes all found preprocesing files]")
   
    parser.add_option('--verbose', '-v', action="store_true", 
                      dest="verbose", default=False, 
                      help="Flag to print verbosely")

    (options, args) = parser.parse_args()

    rootdir=options.rootdir
    verbose = options.verbose
    session = options.session 
     
    # default opts
    movie_num = 0
    concatenate_movies=True
    delete_submovies=False  
    time_in_sec = False
    fmt=None
    # get param files    
    found_param_files = get_param_filepaths(session=session, rootdir=rootdir) 
    for param_fpath in found_param_files:
        with open(param_fpath, 'r') as f:
            params = json.load(f)
            
        for acqdir, paramdict in params.items():
            print("----------------------------------------------------------")
            print("processing: %s" % acqdir)
            print("----------------------------------------------------------")
            pp.pprint(paramdict)
            
            try:
                start_time, end_time = paramdict['times'] 
                if start_time is not None:
                    crop_movie=True
                    print("Specified START-TIME. Cropping from: %s" % str(start_time))
            
                # Check format
                is_avi = len(glob.glob(os.path.join(acqdir, '*.avi'))) > 0
                if not is_avi:
                    assert len(glob.glob(os.path.join(acqdir, '*.mp4')))>0, "No .mp4s found either..."
                    
                fmt = 'avi' if is_avi else 'mp4' 
                if fmt == 'mp4': # This is h.264 file where whole acq. in 1 file
                    movie_num = -1
                    concatenate_movies=False
                    delete_submovies=False  
                else:
                    movie_num = paramdict['movie_num']
                    concatenate_submovies = paramdict['submovie'] in ['true', 'True', True]
                    
                if crop_movie:
                    do_crop(acqdir, start_time, end_time, movie_num=movie_num, 
                            time_in_sec=time_in_sec, fmt=fmt, verbose=verbose)

                if concatenate_submovies:
                    # Concatenate full movie now
                    print("Concatenating submovies: %s" % acqdir)
                    concatenate_subvideos(acqdir)

                # clean up
                cleanup_dir(acqdir, delete_submovies=delete_submovies) 
                
                # move preprocessing params as finished
                done_fpath = '%s.done' % param_fpath
                os.rename(param_fpath, done_fpath)
                
            except Exception as e:
                print("Error processing: %s" % acqdir)
                print("params: %s" % str(params))
                traceback.print_exc()
            
        