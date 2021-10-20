#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 17:07:35 2021

@author: julianarhee
"""
#%%
import os
import glob
from re import I
import cv2
#import scipy.io
import importlib

import numpy as np
import pandas as pd
from pandas.core.base import NoNewAttributesMixin
#import mat73
import pylab as pl

#%%
import flytracker_utils as utils
import matplotlib as mpl

def draw_ellipse(ax, centroid, length, width, angle, asymmetry=0.0, 
        fill=True, edgecolor='none', facecolor='k', alpha=1, **kwargs):
        '''
        Plot an ellipse (adapted from: 
        https://github.com/cta-observatory/ctapipe)

        Parameters
        ----------
        centroid: (float, float)
            Position of centroid
        length: float
            Major axis
        width: float
            Minor axis
        angle: float
            Rotation angle wrt x-axis about the centroid, anticlockwise, in radians
        asymmetry: float
            3rd-order moment for directionality if known
        fill: bool
            Fill ellipse or no
        edgecolor: str or 3-val tuple
            Color of ellipse edge
        facecolor: str or 3-val tuple
            Color of ellipse face (fill should be true)
        alpha: float
            Alpha of ellipse
        kwargs:
            any matplotlib style arguments to pass to the Ellipse patch
        '''
        ellipse = mpl.patches.Ellipse(
            xy=centroid,
            width=length,
            height=width,
            angle=np.degrees(angle),
            fill=fill, edgecolor=edgecolor, facecolor=facecolor,
            alpha=alpha, 
            **kwargs,
        )

        ax.add_patch(ellipse)
        ax.figure.canvas.draw()
        return ellipse


def draw_ellipse_on_array(xpos, ypos, major, minor, theta, 
            height, width, bg_color=255, fill=True, alpha=1,
            facecolor=(0,0,0)):
    '''
    Given ellipse parameters, draw onto array as a frame.
    Note:  Flips array upside down so 0 is at the top (image),
    so coordinates should just be the output of FlyTracker.
    '''
    lw=-1 if fill else 1
    img_arr = np.ones((height, width, 3), dtype=np.uint8)*bg_color
    #ctr = xpos, ypos
    #axes = major, minor
    top_right = (
        (xpos, ypos),      # (x, y)
        (major, minor),   # (full_minor_axis, full_major_axis)
        np.rad2deg(theta), # angle
        -180, 180
    )
    ctr = int(xpos), int(height-ypos)
    axes = int(round(major/2.)), int(round(minor/2.))
    cv2.ellipse(img_arr, ctr, axes, np.rad2deg(theta), -180, 180, (0,0,0), -1)

    if alpha != 1:
        overlay = np.ones((height, width, 3), dtype=np.uint8)*bg_color
        img_arr = cv2.addWeighted(overlay, alpha, img_arr, 1 - alpha, 0)
   
    img = np.flipud(img_arr)

    return img

#%%
def frames_from_traces(df, metadata, fly_id=0, bodypart='body',
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

    count=0
    frames=[]
    for fi, (ix, v) in enumerate(df[df.id==fly_id].iterrows()):
        xpos, ypos, theta, major, minor =  v[['pos_x', 'pos_y', 'ori',\
                    'major_axis_len', 'minor_axis_len']].values
        img = draw_ellipse_on_array(xpos, ypos, major, minor, theta, 
                    height, width, bg_color=255, fill=True)

        if save_images:
            tmp_fpath = os.path.join(dst_dir, '%03d.png' % fi)
            cv2.imwrite(tmp_fpath, img)

        count+=1
        if (n_return_frames is not None) and (count <= n_return_frames):
            frames.append(img)

    return frames



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
                key=utils.natsort)
print("Found %i movies" % len(found_movies))
for m in found_movies:
    print(os.path.split(m)[-1])


#%% Define current movie
curr_movie_path = found_movies[0]
curr_movie = os.path.splitext(curr_movie_path.split('%s/' % src_dir)[-1])[0]
print(curr_movie)

vmeta = utils.get_movie_metadata(curr_movie_path)
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
mov = utils.read_video_as_frames(curr_movie_path, n_frames=20)
print(len(mov))

fig, ax = pl.subplots()
ax.imshow(mov[0])

#%% Load traces from FlyTracker
df = utils.load_tracking(src_dir, curr_movie)
df.shape


importlib.reload(utils)

#%%
fly_ix = 1
bodypart='body'


tmp_dir = utils.create_tmp_frames_dir(vmeta)
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
video_outfile = os.path.join(dst_dir, 'id%i_%s.mp4' % (fly_ix, bodypart))
print(video_outfile)

utils.make_movie_from_frame_dir(video_outfile, tmp_dir, fps=30.)
#utils.save_movie(video_outfile, im_frames, fps=30.)

#%%

utils.remove_tmp_dirs(vmeta)

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

