#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 17:55:34 2021

@author: julianarhee
"""
#%%
import os
import glob
import cv2
import importlib

import numpy as np
import pandas as pd
import pylab as pl

import flytracker_utils as futils
import matplotlib as mpl

from re import I

#%%
#%%
def extracted_params_to_frames(df, metadata, fly_id=0, bodypart='body',
                        n_frames=None, save_images=False, dst_dir=None):
    '''
    Create movie frames from extracted traces. Default is to save all images in 
    tmp folder (in dst_dir) if n_frames is None. 

    Args
    ----
    df (pd.DataFrame)
        Dataframe of extracted traces (from track.mat output of FlyTracker).
    
    metadata (dict)
        Meta info for movie (e.g., height, width, path, etc.)

    fly_id (int)
        ID of fly to track (set to None to draw all flies)
    
    bodypart (str)
        Body part to track (only 'body' so far)
    
    n_frames (None, int)
        None: save all frames to disk in tmp dir
        -1, return all frames
        int, return n_frames

    save_images (bool)
        Save images to tmp dir (for creating movies) 

    dst_dir (None, str)
        Base dir to save /tmp frames to. Must be specified if save_images is True.
        
    Returns
    -------
    frames (list)
        List of np.ndarrays that can be saved as images/video.
    '''
    if n_frames is None:
        save_images = True
    if save_images:
        assert dst_dir is not None, "Must specify dst dir for /tmp frames"
        print("Saving images to tmp dir: %s" % dst_dir)
    
    width = int(metadata['width'])
    height = int(metadata['height'])
    if n_frames==-1:
        n_return_frames = int(metadata['n_frames'])
    elif n_frames is None:
        n_return_frames = None
    else:
        n_return_frames = n_frames
    n_total = int(metadata['n_frames'])

    count=0
    frames=[]
    for fi, (ix, v) in enumerate(df[df.id==fly_id].iterrows()):
        if fi%100==0:
            print(".... processing %i of %i images" % (int(fi+1), n_total))
        xpos, ypos, theta, major, minor =  v[['pos_x', 'pos_y', 'ori',\
                    'major_axis_len', 'minor_axis_len']].values
        img = futils.draw_ellipse_on_array(xpos, ypos, major, minor, theta, 
                    height, width, bg_color=255, fill=True)

        if save_images:
            tmp_fpath = os.path.join(dst_dir, '%03d.png' % fi)
            cv2.imwrite(tmp_fpath, img)

        count+=1
        if (n_return_frames is not None) and (count <= n_return_frames):
            frames.append(img)

    return frames


def create_frames_from_positions(pos_df, major, minor=None, theta=0, 
                                height=400, width=400, 
                                dst_dir=None):
    '''
    Create movie frames from extracted traces. Default is to save all images in 
    tmp folder (in dst_dir) if n_frames is None. 

    Args
    ----
    df (pd.DataFrame)
        Dataframe of extracted positions (from track.mat output of FlyTracker).

    major (int)
        Size of major axis of ellipse

    minor (int)
        Size of minor axis of ellipse (set None to make circle)

    height (int)
        Height of image frame (pixels)

    width (int)
        Width of image frame (pixels) 

    dst_dir (None, str)
        Base dir to save /tmp frames to. Must be specified if save_images is True.
        
    Returns
    -------
    frames (list)
        List of np.ndarrays that can be saved as images/video.
    '''
    print("Saving images to tmp dir: %s" % dst_dir)
    if minor is None:
        minor=major # circle

    n_total = len(pos_df) 
    for fi, (xpos, ypos) in enumerate(pos_df).iterrows()):
        if fi%100==0:
            print(".... processing %i of %i images" % (int(fi+1), n_total))
        img = futils.draw_ellipse_on_array(xpos, ypos, major, minor, theta, 
                    height, width, bg_color=255, fill=True)

        tmp_fpath = os.path.join(dst_dir, '%03d.png' % fi)
        cv2.imwrite(tmp_fpath, img)

    return 


#%% Create args




#%% Select source dirs
rootdir ='/Users/julianarhee/Documents/ruta_lab'
project_dir = os.path.join(rootdir, 'projects', 'tracking', 'examples')

datakey='melF_melM_15mm_1chamber'
src_dir = os.path.join(project_dir, datakey, 'movies')
dst_dir = os.path.join(project_dir, datakey, 'traces')
if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)
print(dst_dir)

fmt = 'avi'
found_movies = sorted(glob.glob(os.path.join(src_dir, '*.%s' % fmt)), \
                key=futils.natsort)
print("Found %i movies" % len(found_movies))
for m in found_movies:
    print(os.path.split(m)[-1])


#%% Define current movie
curr_movie_path = found_movies[0]
curr_movie = os.path.splitext(curr_movie_path.split('%s/' % src_dir)[-1])[0]
print(curr_movie)

vmeta = futils.get_movie_metadata(curr_movie_path)
fps = vmeta['framerate']
width = int(vmeta['width'])
height = int(vmeta['height'])

vmeta
# Movie parameters
#d1=720
#d2=1280
#width=1280
#height=720
#framerate=30.

#%% Load movie for visualization
mov = futils.read_video_as_frames(curr_movie_path, n_frames=20)
print(len(mov))

fig, ax = pl.subplots()
ax.imshow(mov[0])

#%% Load traces from FlyTracker
df = futils.load_tracking(src_dir, curr_movie)
df.shape

importlib.reload(futils)

#%%
bodypart='body'
fly_ix = 0

fly_sex = {0: 'M', 1: 'F'}
mov_basename = '%s_%s' % (bodypart, fly_sex[fly_ix])

futils.remove_tmp_frames_dir(vmeta)
tmp_dir = futils.create_tmp_frames_dir(vmeta)
print(tmp_dir)
im_frames = frames_from_traces(df, vmeta, fly_id=fly_ix,
                bodypart=bodypart, n_frames=20, save_images=True, dst_dir=tmp_dir)
#%%
n_frames_plot=20
fig, axn = pl.subplots(5, 2)
for ix in np.arange(0, n_frames_plot):
    axn[ix, 0].imshow(mov[ix])
    axn[ix, 1].imshow(im_frames[ix])

#%%
video_outfile = os.path.join(dst_dir, '%s.mp4' % (mov_basename))
print(video_outfile)

futils.make_movie_from_frame_dir(video_outfile, tmp_dir, fps=30.)
#futils.save_movie(video_outfile, im_frames, fps=30.)

#%%

futils.remove_tmp_dirs(vmeta)

#

#%% Load segmentations (pixel maps) for body parts
ddict = load_segmentation(curr_movie, src_dir)

#%% Extract frames for a body part
fly_ix = 1
bodypart='body'
frames = seg_to_frames(ddict, bodypart, flyids=[fly_ix], h=height, w=width,
                    bg_color=255, fg_color=0)

fig, ax = pl.subplots()
ax.imshow(frames[0], cmap='gray')
print(frames[0].dtype)

#%% Save video
video_outfile = os.path.join(dst_dir, 'fly_%i.mp4' % fly_ix)
save_movie(video_outfile, frames, fps=framerate)


#%%

#%%

