#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   test.py
@Time    :   2021/11/30 14:52:55
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com

Crop movies

'''

#%%
import os
import re
import glob

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]


#%% Select movie

base_dir = '/media/julianarhee/T7/DATA'
session = '20211203'
src_dir = os.path.join(base_dir, session)

movie_prefix = '20211203_SCx1_co13M_ctnsF_4do_2021-12-03-114157'
movie_num = 3 #-1

if movie_num <0: # get last video
    movie_fpath = sorted(glob.glob(os.path.join(src_dir, '%s*.avi' \
        % movie_prefix)), key=natsort)[0]
else:
    movie_fpath = sorted(glob.glob(os.path.join(src_dir, '%s*%04d.avi' \
        % (movie_prefix, movie_num))), key=natsort)[0]
print(movie_fpath)

#%% Set file name

movie_fname = os.path.basename(movie_fpath)
movie_name, movie_ext = os.path.splitext(movie_fname)

orig_fpath = os.path.join(src_dir, '%s_orig%s' % (movie_name, movie_ext))
#output_fpath = os.path.join(src_dir, '%s%s' % (movie_name, movie_ext))
#print(output_fpath)

# Rewrite original movie
os.rename(movie_fpath, orig_fpath)

#%% Specify how much time to keep
tstamp = '1:00'
minutes, secs = [int(i) for i in tstamp.split(':')]

clip_dur = minutes*60 + secs
start_time=0

#%% Cropy movie and save
ffmpeg_extract_subclip(orig_fpath, start_time, clip_dur, targetname=movie_fpath)



# %%
