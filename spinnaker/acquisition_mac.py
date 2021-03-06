#!/usr/bin/env python3
#%%

from __future__ import (print_function, unicode_literals, division,
                absolute_import)

# from pvapi import PvAPI, Camera
import time
import serial
import sys
import errno
import os
import cv2
import optparse
import json
import threading
import traceback
import numpy as np
import multiprocessing as mp

from queue import Queue
from datetime import datetime
#from scipy.misc import imsave
import imageio

from struct import pack, unpack, calcsize

#from pydc1394 import Camera, DC1394Error
#from pydc1394.camera2 import Context
#
from PIL import Image
#import pyqtgraph as pg
#from pyqtgraph.Qt import QtCore, QtGui
#
from simple_pyspin import Camera
import camera_utils as cutils


#%%
#global first_write
#first_write = 0
def flushBuffer():
    #Flush out serial buffer
    global ser
    tmp=0
    while tmp != '':
        tmp=ser.read()

#%%
def save_camera_info(cam, output_dir='/tmp'): #caminfo_fpath):
    '''Save camera settings to file'''
#    mode_dict = object_fields_dict(cam.mode)
#    mode_dict.pop('setup')
#    with open(caminfo_fpath, 'w') as f:
#        json.dump(mode_dict, f, indent=4)
#
    cam_name = cam.DeviceVendorName.strip() + ' ' + cam.DeviceModelName.strip()
    ofn = os.path.join(output_dir, cam_name.replace(' ', '_') + '.md')
    print('Generating documentation in file: %s' % ofn)

    with open(ofn, 'wt') as f:
        f.write(cam.document())

    return

def object_fields_dict(cam_mode):
    '''Get human-readable dict of cam mode values'''
    mode_dict={}
    for att in dir(cam_mode):
        if not att.startswith('_'):
            try:
                val = getattr(cam_mode,att)
                #print (att, val)
                mode_dict.update({att: val})
            except Exception as e:
                print(att, e) #pass
    return mode_dict

#%%
##def run(options):
#%%
parser = optparse.OptionParser()
parser.add_option('--dst', action="store", dest="dst_dir",
                    default="/home/julianarhee/Videos/flycap",
                    help="out path directory [default: ~/Videos/flycap]")
parser.add_option('--port', action='store', dest='port', default='/dev/ttyACM0',
    help='serial port')

parser.add_option('-E', '--experiment_name', action="store", dest="experiment_name", default="test", help="experiment_name of output file [default: test")
parser.add_option('--output-format', action="store", dest="output_format", type="choice", choices=['png', 'npz'], default='png', help="out file format, png or npz [default: png]")
parser.add_option('--write-process', action="store_true", dest="save_in_separate_process", default=True, help="spawn process for disk-writer [default: True]")
parser.add_option('--write-thread', action="store_false", dest="save_in_separate_process", help="spawn threads for disk-writer")

parser.add_option('-F', '--frame-rate', action="store", dest="framerate",
                    help="requested frame rate", type="float", default=100.0)
parser.add_option('-W', '--width', action="store", dest="width",
                    help="Image width (default: 1080)", type="int", default=960)
parser.add_option('-H', '--height', action="store", dest="height",
                    help="Image height (default: 1080)", type="int", default=960)
parser.add_option('-G', '--gamma', action="store", dest="gamma",
                    help="Image gamma (default: 1.5)", type="float", default=1.5)


parser.add_option('--dur', action="store", dest="recording_duration", help="Recording duration (default: 10min)", type="float", default=10.0)

parser.add_option('--trigger', action="store_true", dest="send_trigger", help="send trigger out to arduino", default=False)
parser.add_option('--stream', action="store_false", dest="save_images", help="Stream only (don't save images)", default=True)

(options, args) = parser.parse_args()
#%%
acquire_images = True
#save_images = True
save_images = options.save_images
send_trigger = options.send_trigger

dst_dir = options.dst_dir
output_format = options.output_format
experiment_name = options.experiment_name

save_in_separate_process = options.save_in_separate_process
recording_duration = float(options.recording_duration)
send_trigger = options.send_trigger
framerate = options.framerate
width = int(options.width)
height = int(options.height)
gamma = float(options.gamma)

frame_period = float(1/framerate)
save_as_png = False
save_as_npz = False
if output_format == 'png':
    save_as_png = True
elif output_format == 'npz':
    save_as_npz = True

port = options.port

print("Recording %.2f min. session @ %.2fHz (img: %ix%i)" % (recording_duration, framerate, width, height))
time.sleep(2)

#%% tmp vars
interactive=False
# dst_dir = '/Users/julianarhee/Documents/ruta_lab/projects/free_behavior/acquisition'
if interactive:
    dst_dir = '/home/julianarhee/Videos/flycap'
    experiment_name = 'test'
    save_as_png = True
    save_in_separate_process = True
    acquire_images = True
    save_images = True
    send_trigger = True
    port = '/dev/ttyACM0'

    framerate = 40.0 #97.0
    width = 1552 #960
    height = 1552 #960
    gamma = 2.0 #1.5
    frame_period = float(1/framerate)

#%%
#set up serial connection

if send_trigger:
    # port = "/dev/cu.usbmodem145201"
    baudrate = 115200

    print("# Please specify a port and a baudrate")
    print("# using hard coded defaults " + port + " " + str(baudrate))
    ser = serial.Serial(port, baudrate, timeout=0.5)
    time.sleep(1)

    #flushBuffer()
    sys.stdout.flush()

    print("Connected serial port...")
else:
    ser=None

#%%
# Make the output paths if it doesn't already exist
try:
    os.makedirs(dst_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise e
    pass
print(dst_dir)

dateformat = '%Y%m%d%H%M%S%f'
tstamp=datetime.now().strftime(dateformat)
dst_dir = os.path.join(dst_dir, '%s_%s' % (experiment_name, tstamp))
print(dst_dir)

try:
    os.makedirs(dst_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise e
    pass

frames_dir = os.path.join(dst_dir, 'frames')
try:
    os.makedirs(frames_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise e
    pass

frametimes_fpath = os.path.join(dst_dir, 'frame_times.txt')
performance_fpath = os.path.join(dst_dir, 'performance.txt')

#%%
# -------------------------------------------------------------
# Recording parameters
# -------------------------------------------------------------
#% -------------------------------------------------------------
# Camera Setup
# -------------------------------------------------------------
cam = None
if acquire_images:
    print('Searching for camera...')
    # try PvAPI
    cameras = []
    pvapi_retries = 50
    # get the camera list
    print('Connecting to camera...')
    # context0 = Context()
    n = 0
    # Let it have a few tries in case the camera is waking up
    while cam is None and n < pvapi_retries:
        try:
            cam = cutils.create_default_camera(framerate=framerate,
                                            width=width, height=height, gamma=gamma) #Camera() #Camera()
            n += 1
            print('\rsearching...')
            time.sleep(0.5)
        except Exception as e:
            print("%s" % e)
            cam = None
print("Bound to PvAPI camera (name: %s)" % (cam.DeviceModelName)) #, cam.guid))

#%% Save camera settings info
#caminfo_fpath = os.path.join(dst_dir, 'caminfo.json')
save_camera_info(cam, dst_dir)

#%%
# -------------------------------------------------------------
# Set up a thread to write stuff to disk
# -------------------------------------------------------------
if save_in_separate_process:
    im_queue = mp.Queue()
else:
    im_queue = Queue()

disk_writer_alive = True

def save_images_to_disk():
    print('Disk-saving thread active...')
    # open time file and set up headers
    time_outfile = open (frametimes_fpath,'w+')
    time_outfile.write('frame_number\tsync_in1\tsync_in2\ttime_stamp\n')

    currdict = im_queue.get()
    while currdict is not None:
        time_outfile.write('%i\t%i\t%i\t%s\n' % (currdict['frame_count'], currdict['sync_in1'], currdict['sync_in2'],currdict['time_stamp']))

        # print name
        if save_as_png:
            imageio.imsave('%s/%s.png' % (frames_dir, currdict['frame_count']), currdict['im_array'])
        else:
            np.savez_compressed('%s/%s.npz' % (frames_dir, currdict['frame_count']), currdict['im_array'])
        #print('... %i' % currdict['frame_count'])

        currdict = im_queue.get()

    disk_writer_alive = False

    print('Disk-saving thread inactive...')
    time_outfile.close()

if save_in_separate_process:
    disk_writer = mp.Process(target=save_images_to_disk)
else:
    disk_writer = threading.Thread(target=save_images_to_disk)
# disk_writer.daemon = True
if save_images:
    disk_writer.daemon = True
    disk_writer.start()
#%%
# Set up viewer
#app = QtGui.QApplication([])
#camviewer = CameraPlot()

cv2.namedWindow('cam_window')
print("Creating streaming window: %ix%i" % (width, height))
win = np.random.rand(width, height)
cv2.imshow('cam_window', win)
time.sleep(1.0)
#%%
#Capture images and save them
# t = 0
report_period = 60*framerate # frames
#record_time = 2. # in sec.
record_time = recording_duration*60.
samp_rate = 1./framerate

if acquire_images:
    #OPEN STREAM
    cam.start()

if send_trigger:
    #byte_string = str.encode('S')
    ser.write(str.encode('S')) #('S')#start arduino trigger
    print('Triggered arduino....')

#%% SAVE FRAMES UNTIL ARDUINO SIGNALS TO STOP
print('Beginning camera acquisition...') 
nframes=0
start_time = time.time()
last_t = start_time
now=start_time
try:
    while time.time()-start_time < record_time:
        if acquire_images:
            n=0
            while (time.time()-now) < samp_rate: #target_time:
                #print('Frame %i: %.3f' % (nframes, time.time()-last_t)
                time.sleep(0.0001)
                n+=1
            now = time.time()
            currt = now-start_time
            curr_frame = cam.get_array() #cam.dequeue()

            im_array = Image.fromarray(curr_frame.copy())
            #print('--- frame_id:%i, %.3f' % (curr_frame.frame_id, currt))

            if save_images:
                fdict = dict()
                fdict['im_array'] = im_array #curr_frame #im_array
                fdict['frame_count'] = nframes
                #fdict['frame_id'] = int(curr_frame.frame_id)
                fdict['sync_in1'] = 0 #meta['s1']
                fdict['sync_in2'] = 0 #meta['s2']
                fdict['time_stamp'] = currt #- start_time
                im_queue.put(fdict)
                #stop saving frames when syncin2 level goes to 0
                #if int(meta['s2'])<1:
                #    break
            nframes += 1
            del curr_frame

            # Show frame
            cv2.imshow('cam_window', np.array(im_array))

            # Break out of the while loop if ESC registered
            key = cv2.waitKey(1)
            #sync_state = camera.LineStatus.GetValue()
            if key == 27: #or sync_state is False: # ESC
                break
            #res.Release()

            if nframes % report_period == 0:
                if last_t is not None:
                    print('avg frame rate: %f ' % (report_period / (currt - last_t)))
                    print('--- frame_id:%i, %.3f' % (nframes, currt))

                last_t=currt
            #print('done')
            #curr_frame.enqueue()

except Exception as e:
    traceback.print_exc()
    #break

print(str.format('total recording time: {} min',(time.time()-start_time)/60))

#%%
# Stop arduino
if send_trigger:
    ser.write(str.encode('F')) #('S')#start arduino trigger
    #ser.write('F')#start arduino trigger
    print('Stopped arduino....')


print('Acquisition Finished!')
#output performance
acq_duration=time.time()-start_time
print('Total Time: %.3f sec' % acq_duration)
expected_frames=int(np.floor(np.around(acq_duration,2)/frame_period))
print('Actual Frame Count = '+str(nframes+1))
print('Expected Frame Count = '+str(expected_frames))

# write performance to file
performance_file = open(performance_fpath,'w+')
performance_file.write('frame_rate\tframe_period\tacq_duration\tframe_count\texpected_frame_count\tmissingFrames\n')
performance_file.write('%10.4f\t%10.4f\t%10.4f\t%i\t%i\t%i\n'%\
    (framerate, frame_period, acq_duration, nframes, expected_frames, expected_frames-nframes))
performance_file.close()

if acquire_images:
    #camera.capture_end()
    cam.close()
    print('Connection closed')

if im_queue is not None:
    im_queue.put(None)

if save_images:
    hang_time = time.time()
    nag_time = 0.05
    sys.stdout.write('Waiting for disk writer to catch up (this may take a while)...')
    sys.stdout.flush()
    waits = 0
    while not im_queue.empty():
        now = time.time()
        if (now - hang_time) > nag_time:
            sys.stdout.write('.')
            sys.stdout.flush()
            hang_time = now
            waits += 1
    print(waits)
    print("\n")

    if not im_queue.empty():
        print("WARNING: not all images have been saved to disk!")

    disk_writer_alive = False
    if save_in_separate_process and disk_writer is not None:
        print("Terminating disk writer...")
        disk_writer.join()
        # disk_writer.terminate()
    # disk_writer.join()
    print('Disk writer terminated')

# close arduino
if ser is not None:
    print('Closing serial connection...')
    ser.close()

print("***** Done! ******")
print('Data saved to: %s' % dst_dir)

#if __name__ == "__main__":
#    run(sys.argv[1:])
