#!/usr/bin/env python3
#%%
from __future__ import (print_function, unicode_literals, division,
                absolute_import)

import errno
import os
import glob
import pandas as pd
import numpy as np
import pylab as pl

import utils as utils

#%%
experiment_name = 'test'
#base_dir = '/Users/julianarhee/Documents/ruta_lab/projects/free_behavior/acquisition'
base_dir = '/home/julianarhee/Documents/flycap'

found_dirs = sorted(glob.glob(os.path.join(base_dir, '%s_*' % experiment_name)), key=utils.natsort)
len(found_dirs)
src_dir = found_dirs[-1] # get most recent



# %%
frametimes_fpath = os.path.join(src_dir, 'frame_times.txt')
assert os.path.exists(frametimes_fpath), 'Path not found: %s' % frametimes_fpath

data = pd.read_csv(frametimes_fpath, sep="\t", header=0)
#%%

#t_diffs = data[data['frame_id']==0]['time_stamp'].diff()
t_diffs =  data['time_stamp'].diff()

fig, ax = pl.subplots()
ax.hist(t_diffs)

t_diffs.describe()



#%%

frames_dir = os.path.join(src_dir, 'frames')
frames = sorted(glob.glob(os.path.join(frames_dir, '*.png')), key=utils.natsort)
print("Found %i frames" % len(frames))

for f in frames[0:20]:
    print(f)


# %%
import cv2
from PIL import Image
from PIL.ExifTags import TAGS

fname = '/Users/julianarhee/Documents/ruta_lab/projects/free_behavior/acquisition/test_20211021180145419616/frames/00000121.bmp'

img = cv2.imread(fname)

image = Image.open(fname)

exifdata = image.getexif()
# iterating over all EXIF data fields
for tag_id in exifdata:
    print(tag_id)
    # get the tag name, instead of human unreadable tag id
    tag = TAGS.get(tag_id, tag_id)
    data = exifdata.get(tag_id)
    # decode bytes 
    if isinstance(data, bytes):
        data = data.decode()
    print(f"{tag:25}: {data}")



# %%
