#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 10:44:33 2021

@author: julianarhee
"""
#%%
import os
import glob
import cv2
import shutil
import threading
import queue
import argparse
import imutils
import time

import numpy as np
import pandas as pd
import pylab as pl

from imutils.video import FPS
import flytracker_utils as futils

#cv2.namedWindow("output", cv2.WINDOW_NORMAL)        # Create window with freedom of dimensions
#im = cv2.imread("earth.jpg")                        # Read image
#imS = cv2.resize(im, (960, 540))                    # Resize image
#cv2.imshow("output", imS)                            # Show image
#cv2.waitKey(0)                                      # Display the image infinitely until any keypress
#
#%%
class FileVideoStream:
    #https://www.pyimagesearch.com/2017/02/06/faster-video-file-fps-with-cv2-videocapture-and-opencv/ 
    def __init__(self, path, queueSize=128):
        '''
        path: str
            Path to input video file
        queue_size: int
            Max n frames to store in queue. Default=128 frames.

        '''
        # initialize the file video stream along with the boolean
        # used to indicate if the thread should be stopped or not
        self.stream = cv2.VideoCapture(path) # instanstiate vid capture object
        self.stopped = False
        # initialize the queue used to store frames read from
        # the video file
        self.Q = queue.Queue(maxsize=queueSize)

    def start(self):
        # start a thread (separate from main thread) to read frames from the file video stream
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # '''Reads and decodes frames from the video file and maintains the queue data structure.'''
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                return
            # otherwise, ensure the queue has room in it
            if not self.Q.full():
                # read the next frame from the file
                (grabbed, frame) = self.stream.read()
                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
                if not grabbed:
                    self.stop()
                    return
                # add the frame to the queue
                self.Q.put(frame)

    def read(self):
        # return next frame in the queue
        return self.Q.get()

    def more(self):
        # return True if there are still frames in the queue
        return self.Q.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

#%%

if __name__=='__main__':
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
    ap.add_argument("--fps", required=False, default=None,
        help="Frame rate to play video (default plays original)")
    ap.add_argument("-W", "--width", required=False, default=400,
        help="Window width, pixels (default: 400)")

    args = vars(ap.parse_args())
    video_fpath = args['video']
    fps = float(args['fps']) if args['fps'] is not None else None
    image_width = int(args['width'])
    fly_ix = 1
    bodypart='body'
    #datakey='melF_melM_15mm_1chamber'
    #project_dir = os.path.join(args['root'], args['experiment'])
    #src_dir = os.path.join(project_dir, datakey, 'traces')
    ##video_outfile = os.path.join(src_dir, 'id%i_%s.mp4' % (fly_ix, bodypart))

#%%
    video_fpath='/Users/julianarhee/Documents/ruta_lab/projects/tracking/examples/melF_melM_15mm_1chamber/traces/id1_body.mp4'

    print(video_fpath)
    assert os.path.exists(video_fpath), \
        'Specified movie does not exist for (fly=%s, bodypart=%s)\n--->%s' % (fly_ix, bodypart, video_fpath)

    #%% faster
    # start the file video stream thread and allow the buffer to
    # start to fill
    print("[INFO] starting video file thread...")
    fvs = FileVideoStream(video_fpath).start()
    time.sleep(1.0)
    # start the FPS timer
    fps_timer = FPS().start()
    mov_meta = futils.get_movie_metadata(video_fpath)
    if fps is None:
        fps = mov_meta['framerate']

    frame_dur = int(np.round((1./fps)*1000))
    print("Requested frame rate %.2f Hz (%.2f ms/frame)" % (fps, frame_dur))

#%%
    # loop over frames from the video file stream
    start_t = time.time()
    n=0
    while (1): #fvs.more():
        t_start=time.perf_counter()
        frame = fvs.read()
        frame = imutils.resize(frame, width=image_width)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = np.dstack([frame, frame, frame])
        # display the size of the queue on the frame
        #cv2.putText(frame, "Queue Size: {}".format(fvs.Q.qsize()),
        #    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)	
        # show the frame and update the FPS counter
        cv2.imshow("Frame", frame)

        n+=1
        fps_timer.update()

        if not fvs.more():
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        while (time.perf_counter()-t_start) < (1/fps):
            pass

    # stop the timer and display FPS information
    fps_timer.stop()
    print("[INFO] elapsed time: {:.2f}".format(fps_timer.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps_timer.fps()))
    total_t = time.time()-start_t
    print("Showed %i frames across %.2fs (~%.2fHz)" % (n, total_t, n/total_t))
    # do a bit of cleanup
    cv2.destroyAllWindows()
    fvs.stop()





#%%
#    # open a pointer to the video stream and start the FPS timer
#    stream = cv2.VideoCapture(video_fpath)
#    fps = FPS().start()
#
#    # loop over frames from the video file stream
#    while True:
#        # grab the frame from the threaded video file stream
#        (grabbed, frame) = stream.read()
#        # if the frame was not grabbed, then we have reached the end
#        # of the stream
#        if not grabbed:
#            break
#        if cv2.waitKey(1) & 0xFF == ord('q'):
#            break
#        # resize the frame and convert it to grayscale (while still
#        # retaining 3 channels)
#        frame = imutils.resize(frame, width=450)
#        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#        frame = np.dstack([frame, frame, frame])
#        # display a piece of text to the frame (so we can benchmark
#        # fairly against the fast method)
##        cv2.putText(frame, "Slow Method", (10, 30),
##            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)	
##        # show the frame and update the FPS counter
#        cv2.imshow("Frame", frame)
#        cv2.waitKey(1)
#        fps.update()
#
#    # stop the timer and display FPS information
#    fps.stop()
#    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
#    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
#    # do a bit of cleanup
#    stream.release()
#    cv2.destroyAllWindows()
#
#
#%%
#
#
#    cap = cv2.VideoCapture(video_outfile)
#    while(cap.isOpened()):
#
#        ret, frame = cap.read() 
#        #cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
#        #cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
#
#        if ret:
#            cv2.imshow("Image", frame)
#        else:
#            print('no video')
#        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#
#        if cv2.waitKey(1) & 0xFF == ord('q'):
#            break
#
#
#    cap.release()
#    cv2.destroyAllWindows()
#
