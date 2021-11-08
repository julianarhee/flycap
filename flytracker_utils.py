#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 17:07:35 2021

@author: julianarhee
"""
#%%
import os
import glob
import cv2
import shutil
import scipy.io

import numpy as np
import pandas as pd
import mat73
import pylab as pl
import re
import matplotlib as mpl

#%% General functions

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]


#%% Drawing functions
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



#%% Movie loading/formatting

def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation = inter)

    # return the resized image
    return resized


def get_movie_metadata(curr_movie_path):
    '''
    Get metadata for specified movie.

    Returns
    -------
    minfo: dict
    '''
    vidcap = cv2.VideoCapture(curr_movie_path)
    success, image = vidcap.read()
    framerate = vidcap.get(cv2.CAP_PROP_FPS)
    width = vidcap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    n_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)

    minfo = {'framerate': framerate,
             'width': width,
             'height': height,
             'n_frames': n_frames,
             'movie_path': curr_movie_path
    }

    vidcap.release()

    return minfo

def read_video_as_frames(curr_movie_path, n_frames=None, n_minutes=None):
    '''
    Read movie as frames, returns list of gray scale images
    '''
    
    meta = get_movie_metadata(curr_movie_path)
    fps = meta['framerate']

    if (n_frames is None and n_minutes is None):
        print("Loading entire movie")
        n_frames = meta['n_frames']

    if n_frames is not None:
        n_minutes = (float(n_frames)/fps)/60.
    elif n_minutes is not None:
        n_frames = (n_minutes*60.) * fps
    print("Loading %.1f min of video (n=%i frames)" % (n_minutes, n_frames))

    frames_list=[]
    vidcap = cv2.VideoCapture(curr_movie_path)
    #success, image = vidcap.read()
    success=True
    count=0
    while success:
        success, image = vidcap.read()
        #print('Read a new frame: ', success)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        frames_list.append(gray)
        count += 1
        if count==n_frames:
            break

    vidcap.release()
    print("done.")
    return frames_list




#%%

def load_tracking(src_dir, curr_movie):
    '''
    Load track.mat from FlyTracker output dir.

    Args:
    -----
    src_dir: (str, path)
        Path to base results dir ("Output" dir specified in FlyTracker)

    curr_movei: (str)
        Name of movie analyzed (parent dir containing .mat output files)

    Returns:
    -------
    df: (pd.DataFrame)
        Dataframe of all the extracted data from FlyTracker.
        Rows are frames, columns are features (including fly ID, 'id')
    '''
    ft_outfile = glob.glob(os.path.join(src_dir, curr_movie, '*track.mat'))[0]
    #print(ft_outfile)

    mat = scipy.io.loadmat(ft_outfile)
    mdata = mat.get('trk')

    # Use fields to create dict
    # 'names' (1, 35) 
    # 'data' (n_flies, n_frames, n_fields)
    # 'flags' (possible switches, check with flytracker/visualizer)
    mdtype = mdata.dtype
    ndata = {n: mdata[n][0, 0] for n in mdtype.names}

    columns = [n[0].replace(' ', '_') for n in ndata['names'][0]]
    n_flies, n_frames, n_flags = ndata['data'].shape
    d_list=[]
    for fly_ix in range(n_flies):
        df_ = pd.DataFrame(data=ndata['data'][fly_ix, :], columns=columns)
        df_['id'] = fly_ix
        d_list.append(df_)
    df = pd.concat(d_list, axis=0, ignore_index=True)
    return df


def load_segmentation(curr_movie, src_dir):
    '''
    Loads segmentation.mat corresponding to specified movie from src_dir.

    Args:
    -----
    curr_movie: (str)
        Name of movie, i.e., parent dir of segmentations.mat

    src_dir: (str, path)
        Path to FlyTracker results dir.

    Returns:
    
    ddict: (dict)
        ddict['seg']: list of n_frames elements (N=n_frames)
        ddict['seg'][frame_ix][0]: list of n_flies elements
        ddict['seg'][frame_ixl][0][fly_ix]: dict
        keys: ('body', 'legs', 'rem', 'wings')
    '''
    # Create array to match Matlab array view
    # np.unravel_index(cpixels[2], sz, order='C') # sz=(720, 1280)
    # img_r = np.reshape(img, sz, order='F')
    # ax.imshow(img_r)
    seg_outfile = glob.glob(os.path.join(src_dir, curr_movie, '*seg.mat'))[0]
    #print(seg_outfile)
    try:
        segmat = scipy.io.loadmat(seg_outfile)
    except NotImplementedError:
        ddict = mat73.loadmat(seg_outfile)
    return ddict


def seg_to_frames(ddict, bodypart, flyids=[], h=720, w=1280, 
                    bg_color=255, fg_color=0, data_type=np.uint8):
    '''
    Given data dict loaded with h5py (segmentation.mat),
    parse into frames.

    Args:
    ----   
    ddict: (dict)
        f
    Returns:
    -------- 
    img_list: (list)
        List of frames matching specified dims

    '''
    n_frames = len(ddict['seg'])
    if len(flyids)==0:
        flyids = np.arange(0, len(ddict['seg'][0][0]))
    fc = 1*fg_color if bg_color==0 else 0
    sz = (h, w)
    img_list=[]
    for frame_ix in range(n_frames):
        img = np.ones((h*w,), dtype=data_type)*bg_color
        for flyid in flyids:
            cdict = ddict['seg'][frame_ix][0][flyid]
            cpixels = cdict[bodypart].astype(int)
            img[cpixels]=fc
        img_r = np.reshape(img, sz, order='F')
        img_list.append(img_r)
    return img_list


#%%

def create_tmp_frames_dir(metadata):
    '''Create /tmp dir for image arrays as frames for movies. Default uses
    current movie base dir 
    '''
    base_dir = metadata['movie_path'].split('/movies')[0]
    dst_dir = os.path.join(base_dir, 'traces', 'tmp')
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    # Delete old files
    if os.path.exists(dst_dir):
        old_files = glob.glob(os.path.join(dst_dir, '*.png'))
        for f in old_files:
            os.remove(f)

    return dst_dir

def remove_tmp_frames_dir(metadata):
    '''Remove /tmp dir for image arrays as frames for movies. Default uses
    current movie base dir 
    '''
    base_dir = metadata['movie_path'].split('/movies')[0]
    dst_dir = os.path.join(base_dir, 'traces', 'tmp')
    print("Removing tmp frames dir: %s" % dst_dir)
    # Delete old files
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)

    return



def save_movie(video_outfile, frames, fps=30.):
    '''
    Saves .png to a temp folder, then converts to movie.

    Args:
    ----
    video_outfile: (str, path)
        Full path to output movie file
    
    frames: (list)
        List of frames (dtype=np.uint8)
    
    fps: (float)
        Framerate of output video.
    '''
    dst_dir = os.path.split(video_outfile)[0]
    tmpdir = os.path.join(dst_dir, 'tmp')
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    # Delete old files
    if os.path.exists(tmpdir):
        old_files = glob.glob(os.path.join(tmpdir,'*.png'))
        for f in old_files:
            os.remove(f)
    for fi, frame in enumerate(frames):
        tmp_fpath = os.path.join(tmpdir, '%03d.png' % fi)
        cv2.imwrite(tmp_fpath, frame)

    cmd='ffmpeg -y -r ' + '%.3f' % fps \
        + ' -i ' + tmpdir+'/%03d.png \
        -vcodec libx264 -f mp4 \
        -pix_fmt yuv420p ' + video_outfile
    os.system(cmd)
    print("... ...done")

    return

def make_movie_from_frame_dir(video_outfile, tmp_dir, fps=30.):
    '''
    Loads .png from tmp_dir, $converts to movie.

    Args:
    ----
    video_outfile: (str, path)
        Full path to output movie file
    
    tmp_dir: (str, path)
        Path to /tmp dir with movie frames.

    fps: (float)
        Framerate of output video.
    '''
    assert os.path.exists(tmp_dir), "Tmp dir does not exist: %s" % tmp_dir

    found_frames = sorted(os.listdir(tmp_dir), key=natsort)
    assert len(found_frames)>0, "No frames found: %s" % tmp_dir

    cmd='ffmpeg -y -r ' + '%.3f' % fps \
        + ' -i ' + tmp_dir+'/%03d.png \
        -vcodec libx264 -f mp4 \
        -pix_fmt yuv420p ' + video_outfile
    os.system(cmd)
    print("... ...done")

    return

