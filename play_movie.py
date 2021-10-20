#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 14:04:10 2021

@author: julianarhee
"""
#%%
import os
import argparse
import traceback
import time
#from psychopy import visual, monitors
from psychopy import visual, core, event, constants, monitors
#from psychopy.constants import (PLAYING, PAUSED) 
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED

import psychopy
from pyglet.window.key import I
psychopy.prefs.hardware['audioLib'] = ['PTB', 'sounddevice', 'pyo','pygame']
#print(prefs)



#%%

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-R", "--root", required=False, help="Path to data root",
    default='/Users/julianarhee/Documents/ruta_lab/projects/tracking')
ap.add_argument('-E', '--experiment', required=False, help='Experiment dir',
    default='examples')
ap.add_argument('-k', '--datakey', required=False, help='datakey',
    default='melF_melM_15mm_1chamber')
ap.add_argument("-v", "--video", required=True,
    help="Full path to input video file")

ap.add_argument('-M', '--monitor', required=False, 
    help='Monitor to draw on (default, test)', default='test')

ap.add_argument('-H', '--display_height', required=False, 
    help='Display size, pixels(default, 400)', default=400)

ap.add_argument('-W', '--display_width', required=False, 
    help='Display width, pixels(default, 600)', default=600)

args = vars(ap.parse_args())
video_fpath = args['video']
monitor_name = args['monitor']

display_width = int(args['display_width'])
display_height = int(args['display_height'])

#%%
video_fpath='/Users/julianarhee/Documents/ruta_lab/projects/tracking/examples/melF_melM_15mm_1chamber/traces/id1_body.mp4'
display_width, display_height = (600, 400)
#display_pos = (0,100)
monitor_name='test'

#fly_ix = 1
#bodypart='body'
#datakey='melF_melM_15mm_1chamber'
#project_dir = os.path.join(args['root'], args['experiment'])
#src_dir = os.path.join(project_dir, datakey, 'traces')
##video_outfile = os.path.join(src_dir, 'id%i_%s.mp4' % (fly_ix, bodypart))
print(video_fpath)
assert os.path.exists(video_fpath), \
    'Specified movie does not exist:\n--->%s' % (video_fpath)

# Select monitor 
try:
    saved_calibs = monitors.getAllMonitors()
    assert monitor_name in saved_calibs, \
        "Monitor [%s] not found. Existing calibs: %s" % (monitor_name, str(saved_calibs))
except AssertionError as e:
    traceback.print_exc()

# Select monitor 
mon = monitors.Monitor(monitor_name) # fetch the most recent calib for this monitor
# Create drawing window 
win = visual.Window(size=[display_width, display_height], 
    monitor=mon, units='pix') #pos=display_pos)


#%%
mov = visual.MovieStim3(win, video_fpath, flipVert=False,units='pix') #size=(320, 240), units='pix')
# give the original size of the movie in pixels:
#print(mov.format.width, mov.format.height)
print('orig movie size=%s' % mov.size)
print('duration=%.2fs (fps=%.2fHz)' % (mov.duration, mov.getFPS()))
globalClock = core.Clock()


#%%
mov.play()
while mov.status != FINISHED and mov.status!=STOPPED:
    #print(mov.status)
    if mov.status == PLAYING:
        mov.draw()
        win.flip()
    #print(event.getKeys())
    for key in event.getKeys():
        if key in ['escape','q']:
            mov.stop()
            print(mov.status)
            win.close()
            core.quit()
            #break
        elif key in ['p']:
            # To pause the movie while it is playing....
            if mov.status == PLAYING:
                print('PAUSED')
                mov.pause()
            elif mov.status == PAUSED:
                print('RESUMING')
                # To /unpause/ the movie if pause has been called....
                mov.play()
                win.flip()
    print('.')

print('here.')