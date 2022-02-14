#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   read_abt.py
@Time    :   2022/02/01 16:35:28
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''
#%%
import os

import glob
import re #from re import A, I

import pyabf

import numpy as np
import pylab as pl
import pandas as pd

#%%

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]


#%%
audio_src = '/home/julianarhee/Projects/sound-chamber/clampx-files'
video_src = '/home/julianarhee/Videos/basler'

#%%
# Read audio file
session = '2022_02_01'
abf_fpath = glob.glob(os.path.join(audio_src, '%s*.abf' % session))[0]
print(abf_fpath)
abf = pyabf.ABF(abf_fpath)
print(abf.sweepY) # displays sweep data (ADC)
print(abf.sweepX) # displays sweep times (seconds)
print(abf.sweepC) # displays command waveform (DAC)


fig, ax = pl.subplots()
pl.plot(abf.sweepX, abf.sweepY)

#%%

os.listdir(video_src)

cap = '20220201-160121_sim_5do_sh'
vid_dir = os.path.join(video_src, cap)
assert os.path.exists(vid_dir)
frame_dir = os.path.join(vid_dir, 'frames')

#%%
performance_info = os.path.join(vid_dir, 'performance.txt')
metadata = pd.read_csv(performance_info, sep="\t")
metadata
fps = float(metadata['frame_rate'])
     
     
os.listdir(frame_dir) 
#%%
rename_files=False
if rename_files:
    fns = sorted(glob.glob(os.path.join(frame_dir, '*.png')), key=natsort) 
    print("Found %i files" % len(fns))

    f = fns[0]
    for f in fns:
        fdir, fname = os.path.split(f)
        fnum_ext = fname.split('_')[0]
        fnum = int(os.path.splitext(fnum_ext)[0])
        fname_new = os.path.join(frame_dir, '%06d.png' % fnum)
        assert not os.path.exists(fname_new), "Path exists: %s" % fname_new
        os.rename(f, fname_new)
        

fns = sorted(glob.glob(os.path.join(frame_dir, '*.png')), key=natsort) 
print("Found %i files" % len(fns))
fns[0:20]    
      
#%% save movie 
outfile = os.path.join(vid_dir, '%s.avi' % cap)
print(outfile) 

print(len(os.listdir(frame_dir)))

#cmd='ffmpeg -y -r ' + '%.3f' % fps + ' -i ' + frame_dir+'/%d.png -vcodec libx264 -f avi -pix_fmt yuv420p ' + outfile
cmd='ffmpeg -y -r ' + '%.3f' % fps + ' -i ' + frame_dir+'/%d.png -vcodec libx264 -f avi ' + outfile

os.system(cmd)

cmd='ffmpeg -y -r ' + '%.3f' % fps + ' -i ' + frame_dir+'/%d.png -vcodec libx264 -f avi ' + outfile


cmd='ffmpeg -y -r ' + '%.2f' % fps + ' -i ' + frame_dir+'/%06d.png -c:v qtrle -pix_fmt rgb24 ' + outfile
cmd
os.system(cmd)

