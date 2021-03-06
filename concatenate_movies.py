#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   concatenate_movies.py
@Time    :   2022/02/02 17:47:49
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''
#%%
import os
import glob
import re
import subprocess
import shlex
import shutil
import sys
import optparse
import time
natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]

def create_movie_input_file(found_movies):
    parent_dir, _ = os.path.split(found_movies[0])
    outfile = os.path.join(parent_dir, 'movlist.txt')
    fnames = sorted([os.path.split(fn)[-1] for fn in found_movies], 
                    key=natsort) 
    if os.path.exists(outfile):
        os.remove(outfile)
    with open(outfile, 'a') as fp:
        for fn in fnames:
            fp.write('file \'%s\'\n' % fn)
    return

def get_subvideos(acq_dir):
    '''
    From acquisition directory (parent dir of saved .avi files), get
    sorted list of all subvideos to concatenate into 1 big movie.
    This is due to movies saved as chunks using FlyCapture.
    '''
    parentdir, acqname = os.path.split(acq_dir)
    found_movies = glob.glob(os.path.join(acq_dir, '%s*.avi' % acqname))
    found_movies
    # check that all are the same acquisition
    all_datestrs = list(set([re.search('\d{4}-\d{2}-\d{2}-\d{6}', f).group() \
            if re.search('\d{4}-\d{2}-\d{2}-\d{6}', f) is not None else None \
            for f in found_movies]))
    datestrs = [f for f in all_datestrs if f is not None]
    assert len(datestrs)==1, "Too many datestr found: %s" % str(datestrs)
    datestr = datestrs[0]

    found_movies = sorted(glob.glob(os.path.join(acq_dir, '%s*%s*.avi' \
        % (acqname, datestr))), key=natsort)

    return found_movies


def cleanup_dir(acq_dir, delete_submovies=False):
    '''
    Move (or delete) subvideos after making full concatenated video.
    Also checks for .orig avis to move.
    '''
    # Find sub videos
    found_movies = get_subvideos(acq_dir)
    
    # Move subvideos
    submov_dir = os.path.join(acq_dir, 'subvideos')
    if not os.path.exists(submov_dir):
        os.makedirs(submov_dir)
    for submov_path in found_movies:
        old_dir, submov_name = os.path.split(submov_path)
        shutil.move(submov_path, os.path.join(submov_dir, submov_name))

    # Check if there are .orig files to move
    orig_files = glob.glob(os.path.join(acq_dir, '*.orig'))
    for orig_path in orig_files:
        old_dir, submov_name = os.path.split(orig_path)
        shutil.move(orig_path, os.path.join(submov_dir, submov_name))
        
    # Delete dir if desired
    if delete_submovies:
        confirm = input("Are you sure you want to delete submovies? Enter Y/n: ")
        if confirm=='Y':
            confirm_again = input("Type 'yes' to confirm: ")
            if confirm=='yes':
                shutil.rmtree(submov_dir)
            
    return 

def concatenate_subvideos(acq_dir, delete_submovies=False):
    '''
    For a given acquisition (set of .avi files)
    1. Check that all submovies are of the same capture. 
    2. Create 1 concatenated movie.
    3. Clean up submovies into dir (tmp, maybe delete). 
    
    Args:
    -----
    acq_dir: (str)
        Path to acquisition dir containing sub movie .avi files
    
    delete_submovies: (bool)
        Set to True to delete sub videos (otherwise, moves them to tmp folder).
    '''
    # Find sub videos
    found_movies = get_subvideos(acq_dir)

    # Create list of subvideos for concatenating
    create_movie_input_file(found_movies)

    # Create output movie path
    parentdir, acqname = os.path.split(acq_dir)
    outpath = os.path.join(acq_dir, '%s.avi' % acqname)
    
    # Check that we didn't already make the movie    
    if os.path.exists(outpath):
        print("Concatenated movie exists!! %s.\nAborting" % outpath)
        return
 
    # Concatenate movies in list
    print('Creating full movie: %s' % outpath)
    list_fpath = os.path.join(acq_dir, 'movlist.txt')
    cmd = 'ffmpeg -f concat -i %s -c copy %s' % (list_fpath, outpath)
    subprocess.call(shlex.split(cmd))


    return outpath

#%%

def extract_options(options):

    parser = optparse.OptionParser()
    parser.add_option('--rootdir', action="store", 
                      dest="rootdir", default='/mnt/sda/Videos', 
                      help="out path directory [default: /mnt/sda/Videos]")

    parser.add_option('-E', '--assay', action="store", 
                      dest="assay", default='single_20mm_1x1', 
                      help="Name of dir containing acquisition subdirs, e.g., ")

    parser.add_option('-S', '--session', action="store", 
                       dest='session', default=None, 
                       help='session (YYYYMMDD), specify to process >1 acquisition')
  
    parser.add_option('-A', '--acquisition', action="store", 
                       dest='acquisition', default=None, 
                       help='Name of acquisition, or dir containing .avi files to concatenate (default grabs all dirs found in SESSION dir)')

    parser.add_option('--delete', action="store_true", dest="delete_submovies", default=False, help="Delete sub-videos after concatenating")

    (options, args) = parser.parse_args()

    return options

rootdir = '/mnt/sda/Videos'
assay = 'single_20mm_triad_2x1'
acquisition = '20220202-1152_triad_mauW_7do_sh'

if __name__ == '__main__':

    opts = extract_options(sys.argv[1:])
    #rootdir='/mnt/sda/Videos'
    #assay='singlechoice_20mm_1x_sessions'
    #session = '20220202'

    rootdir = opts.rootdir
    assay = opts.assay
    session = opts.session
    acquisition = opts.acquisition
    delete_submovies = opts.delete_submovies
    
    # -*- coding: utf-8 -*-
    basedir = os.path.join(rootdir, assay)
    
    if acquisition is None: 
        assert session is not None, "Must provide session or acquisition."
        found_acqs = sorted(glob.glob(os.path.join(basedir, #session, 
                                            '%s-*' % session)), key=natsort)
    else:
        found_acqs = list(set(glob.glob(os.path.join(basedir, #session, 
                                            '%s*' % acquisition))))
        assert len(found_acqs)==1, \
            "Found %i acquisitions that match:\n %s" % (len(found_acqs), str(acquisition))
         
    # exampe
    print("Preprocessing %i acquisitions." % len(found_acqs))
    acq_dir = found_acqs[0]
    for acq_dir in found_acqs:
        print("-------------------------------------------")
        print('%s' % acq_dir)
        print("-------------------------------------------")
        t = time.time()
        concatenate_subvideos(acq_dir)
        elapsed = time.time() - t
        print("Elapsed: %.2f" % elapsed)
        # Clean up
        cleanup_dir(acq_dir, delete_submovies=delete_submovies)
