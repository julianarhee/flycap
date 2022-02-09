#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   crop_movies.py
@Time    :   2021/11/30 14:52:55
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com

Crop movies

'''

#%%
import sys
import os
import re
import glob
import optparse
import time
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import concatenate_movies as conc
#from concatenate_movies import concatenate_subvideos

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]

def get_start_and_end_sec(start_time, end_time, time_in_sec=False):
    '''
    Get start and end time in sec.
    
    Args:
    -----
    start_time, end_time: (str or float)
        If str, must be format:  'MM:SS.ms' (estimated with VLC)
        If int, assumes all the way to end (100)
       
    time_in_sec: (bool)
        If INT provided for either start_time or end_time, specifies whether the number is in seconds or minutes
        Set to False if in minutes (e.g., 100 minutes to get full video, a big number). 
    '''
    tstamps=[] 
    for tstamp in [start_time, end_time]:
        if isinstance(tstamp, str):
            # Get start time in sec 
            minutes, secs = [float(i) for i in tstamp.split(':')]
            #print(minutes, secs)
            tstamp_sec = minutes*60. + secs
        else:
            tstamp_sec = float(tstamp) if time_in_sec else float(tstamp)*60. 
        tstamps.append(tstamp_sec) 

    return tstamps[0], tstamps[1]

def crop_movie(input_movie, start_time, end_time, time_in_sec=False):
    '''
    Crop specified movie.
    
    Args:
    -----
    input_movie: (str)
        Full path to movie to crop.
    
    start_time, end_time: (str or float)
        If str, must be format:  'MM:SS.ms' (estimated with VLC)
        If int, assumes all the way to end (100)
       
    time_in_sec: (bool)
        If INT provided for either start_time or end_time, specifies whether the number is in seconds or minutes
        Set to False if in minutes (e.g., 100 minutes to get full video, a big number). 

    '''
    orig_input_fpath = input_movie
    input_movie = '%s.orig' % orig_input_fpath 
    
    # Make sure movie not already cropped
    if os.path.exists(input_movie):
        print("Movie already cropped, check: %s\n Aborting CROP." % input_movie)
        return
        
    os.rename(orig_input_fpath, input_movie) # Rename original input movie 
    output_movie = orig_input_fpath # Replace orig input movie name with new movie (for later concatenating)   

    #output_movie = os.path.join(acqdir, '%s_trimmed%s' % (acquisition, movie_ext))
    print("Input: %s" % input_movie)
    print("Output: %s" % output_movie)

    # Specify how much time to keep
    start_time_sec, end_time_sec = get_start_and_end_sec(start_time, end_time, 
                                                 time_in_sec=time_in_sec)
    print('Start/end time (sec): %.2f, %.2f' % (start_time_sec, end_time_sec))
 
    # Cropy movie and save
    t = time.time()
    ffmpeg_extract_subclip(input_movie, start_time_sec, end_time_sec, 
                        targetname=output_movie)
    elapsed = time.time() - t
    print(elapsed)

    return


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

    parser.add_option('--submovie', action="store_true", 
                      dest="is_submovie", default=False, 
                      help="Vid to crop is a subvideo")
    parser.add_option('-N', '--num', action="store", 
                      dest="movie_num", default=-1, type=int, 
                      help="Movie number (suffix, or -1 for FULL")
    parser.add_option('-s', '--start', action="store", 
                      dest="start_time", default=0, 
                      help="Start time (sec or min). If str, MM:SS.ms")
    parser.add_option('-e', '--end', action="store", 
                      dest="end_time", default=0, 
                      help="End time (sec or min). If str, MM:SS.ms. Specify large number and time_in_sec=False to go to end.")
    parser.add_option('--seconds', action="store_true", 
                      dest="time_in_sec", default=False, 
                      help="If number provided for start or end time, specifies whether is in MIN or SEC.")

    parser.add_option('--cat', action="store_true", 
                      dest="concatenate_submovies", default=False, 
                      help="Create concatenated videos from submovies")
    parser.add_option('--delete', action="store_true", 
                      dest="delete_submovies", default=False, 
                      help="Delete sub-videos after concatenating")

    (options, args) = parser.parse_args()

    return options

rootdir = '/mnt/sda/Videos'
assay = 'single_20mm_triad_2x1'
acquisition = '20220203-1101_triad_yak_7do_sh'
is_submovie=True
movie_num=0
start_time0 = '00:05'
end_time=100
time_in_sec=False
delete_submovies=False

#%%
if __name__ == '__main__':

    opts = extract_options(sys.argv[1:])
#    base_dir = '/mnt/sda/Videos'
#    experiment = 'singlechoice_20mm_1x_sessions'
#    session = '20220202'
#    acqname = '20220202-1146_rsim_7do_sh' #'20211203_SCx1_co13M_ctnsF_4do_2021-12-03-114157'
#    movie_num = 0 #-1 #3 #-1
#    is_submovie=True
#
    rootdir = opts.rootdir
    assay = opts.assay
    session = opts.session
    acquisition = opts.acquisition
          
    is_submovie = opts.is_submovie
    movie_num = opts.movie_num
    start_time = opts.start_time #'00:06.75'
    end_time = opts.end_time # 100 #'32:38.0'
    time_in_sec = opts.time_in_sec

    delete_submovies = opts.delete_submovies
    concatenate_submovies = opts.concatenate_submovies
     
#%% 
    # Format start/end time
    start_time = start_time if (isinstance(start_time, str) and ':' in start_time) \
            else float(start_time) 
    end_time = end_time if (isinstance(end_time, str) and ':' in end_time) \
            else float(end_time)       

#%% 
    # Get src dirs
    basedir = os.path.join(rootdir, assay) 
    acqdir = os.path.join(basedir, acquisition)    

    # Check if video to crop is actually a subvideo 
    if is_submovie:
        subvid_dir = os.path.join(basedir, acquisition, 'subvideos')
        if os.path.exists(subvid_dir):
            acqdir = subvid_dir
        else:
            acqdir = os.path.join(basedir, acquisition)
    print("Processing acq.: %s" % acqdir)

#%%
    if movie_num <0: # get last video
        input_movie = sorted(glob.glob(os.path.join(acqdir, '%s*.avi' \
            % acquisition)), key=natsort)[0]
    else:
        input_movie = sorted(glob.glob(os.path.join(acqdir, '%s*%04d.avi' \
            % (acquisition, movie_num))), key=natsort)[0]
    print("Cropping: %s" % input_movie)

    crop_movie(input_movie, start_time, end_time, time_in_sec=time_in_sec)
    
#%% 
    # Rename original input movie
    movie_fname = os.path.basename(input_movie)
    movie_name, movie_ext = os.path.splitext(movie_fname)

# %%
    if concatenate_submovies:
        # Concatenate full movie now
        print("Concatenating submovies: %s" % acqdir)
        conc.concatenate_subvideos(acqdir)
        conc.cleanup_dir(acqdir, delete_submovies=delete_submovies)

# Trim full movie:  152.11sec.
# Trim subvideo: 34.97sec


