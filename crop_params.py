#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   crop_params.py
@Time    :   2022/02/11 13:04:53
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''
import sys
import os
import glob
import json
import re
import optparse

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]

#%%

    
def set_crop_params(session, assay_prefix='single_20mm', rootdir='/mnt/sda/Videos'):
    '''
    Finds all acquisitions run on a given day (YYYYMMDD), including diff assays, and
    uses user input to specify crop start/end times, and submovie status, etc.
    
    Saves param info to: 
        <rootdir>/<assaydir>/<SESSION_preprocessing.json
        
    {path_to_acquisition: 
        {'times': (start_t, end_t),
         'submovie': True/False,
         'movie_num': 0}
    }
    
    '''
    found_acqs0 = sorted(glob.glob(os.path.join(rootdir, '%s*' % assay_prefix, '%s-*' % session)), key=natsort)
    found_acqs = [fdir for fdir in found_acqs0 if os.path.isdir(fdir)] 
    print(found_acqs)

    found_assays = list(set([fp.split(rootdir+'/')[-1].split('/'+session)[0] for fp in found_acqs]))

    print('------------------------------------------------------')
    print("Found %i assays." % (len(found_assays)))
    for curr_assay in found_assays:
        # Check for existing params
        fname = '%s_preprocessing.json' % session
        proc_input_file = os.path.join(rootdir, curr_assay, fname)
        if os.path.exists(proc_input_file):
            with open(proc_input_file, 'r') as f:
                procdict = json.load(f)
        else:
            procdict={}

        print('------------------------------------------------------')
        curr_acqs = [fdir for fdir in 
                     sorted(glob.glob(os.path.join(rootdir, curr_assay, '%s-*' % session)), key=natsort)
                     if os.path.isdir(fdir)]
        print("[%s] - Found %i acquisitions" % (curr_assay, len(curr_acqs)))

        # Check which acqs already have params
        existing_params = [k for k in curr_acqs if k in procdict.keys()] 
        
        for acq in curr_acqs:
            if acq in existing_params:
                print("[%s] Found existing params" % acq)
                print(procdict[acq])
                preprocess = input("Overwrite? Y/n:")
            else: 
                preprocess = input("    %s | Enter Y/n to peprocess: " % acq)

            confirmed=False 
            if preprocess == 'Y':
                submovie = input('Is this a submovie? (ends .avi if FlyCap), Enter Y/n: ')
                is_submovie = submovie=='Y'
                if is_submovie:
                    mnum = input('Enter movie number (0-start): ')
                    movie_num = int(mnum)
                else:
                    movie_num = -1
                while not confirmed:
                    start_t = input("Enter start time ('00:00.0' in minutes:seconds.msec): ") 
                    end_t = input('Enter end time (hit ENTER to go to end of movie): ')
                    if end_t is None or end_t=='':
                        end_t = 100
                    confirm = input("Start: %s, End: %s. Press Y/n to confirm: " % (str(start_t), str(end_t)))
                    confirmed = confirm=='Y'
                    
                procdict.update({acq: {'times': (start_t, end_t),
                                    'submovie': is_submovie,
                                    'movie_num': movie_num}})

        if len(procdict.keys())>0:
            with open(proc_input_file, 'w') as f:
                json.dump(procdict, f, sort_keys=True)
                        
    return proc_input_file


def extract_options(options):

    parser = optparse.OptionParser()
    parser.add_option('--rootdir', action="store", 
                      dest="rootdir", default='/mnt/sda/Videos', 
                      help="out path directory [default: /mnt/sda/Videos]")

    parser.add_option('-E', '--assay-prefix', action="store", 
                      dest="assay_prefix", default='single_20mm', 
                      help="Prefix of assay (e.g., single_20mm) ")

    parser.add_option('-S', '--session', action="store", 
                       dest='session', default=None, 
                       help='session (YYYYMMDD), specify to process >1 acquisition')
   
    (options, args) = parser.parse_args()

    return options


#%%

rootdir = '/mnt/sda/Videos'
assay_prefix = 'single_20mm'
session = '20220209'

if __name__ == '__main__':

    opts = extract_options(sys.argv[1:])

    rootdir = opts.rootdir
    assay_prefix = opts.assay_prefix
    session = opts.session
          
    # if .avi (subvideos), if .mp4 (h.264)

    fn = set_crop_params(session, assay_prefix=assay_prefix, rootdir=rootdir)
    
