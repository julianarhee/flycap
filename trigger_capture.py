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
import optparse
import json
import threading

import numpy as np
import multiprocessing as mp

from queue import Queue
from datetime import datetime
#from scipy.misc import imsave
import imageio

from struct import pack, unpack, calcsize

from pydc1394 import Camera, DC1394Error
from pydc1394.camera2 import Context

from PIL import Image

#%%

def save_camera_info(cam0, caminfo_fpath):
    '''Save camera settings to file'''
    mode_dict = object_fields_dict(cam0.mode)
    mode_dict.pop('setup')
    with open(caminfo_fpath, 'w') as f:
        json.dump(mode_dict, f, indent=4) 

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

parser = optparse.OptionParser()
parser.add_option('--output-path', action="store", dest="base_dir", default="/tmp/frames", help="out path directory [default: /tmp/frames]")
parser.add_option('--experiment_name', action="store", dest="experiment_name", default="test", help="experiment_name of output file [default: test")
parser.add_option('--output-format', action="store", dest="output_format", type="choice", choices=['png', 'npz'], default='png', help="out file format, png or npz [default: png]")
parser.add_option('--write-process', action="store_true", dest="save_in_separate_process", default=True, help="spawn process for disk-writer [default: True]")
parser.add_option('--write-thread', action="store_false", dest="save_in_separate_process", help="spawn threads for disk-writer")
parser.add_option('--frame-rate', action="store", dest="frame_rate", help="requested frame rate", type="float", default=40.0)
parser.add_option('--trigger', action="store_true", dest="send_trigger", help="send trigger out to arduino", default=False)

(options, args) = parser.parse_args()

acquire_images = True
save_images = True
send_trigger = options.send_trigger

base_dir = options.base_dir
output_format = options.output_format
experiment_name = options.experiment_name

save_in_separate_process = options.save_in_separate_process
frame_rate = options.frame_rate
frame_period = float(1/frame_rate)

save_as_png = False
save_as_npz = False
if output_format == 'png':
    save_as_png = True
elif output_format == 'npz':
    save_as_npz = True

#%% tmp vars
experiment_name = 'test'
base_dir = '/Users/julianarhee/Documents/ruta_lab/projects/free_behavior/acquisition'
frame_rate=40.

frame_period = float(1/frame_rate)
save_as_png = True
save_in_separate_process = True

acquire_images = True
save_images = True
send_trigger = False

#%% Make the output paths if it doesn't already exist
try:
    os.makedirs(base_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise e
    pass
print(base_dir)

dateformat = '%Y%m%d%H%M%S%f'
tstamp=datetime.now().strftime(dateformat)
dst_dir = os.path.join(base_dir, '%s_%s' % (experiment_name, tstamp))
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
#parameters
#samp_rate = 10 #in hertz
#record_time = 60*2 #in seconds

if send_trigger:
    #saves starting temp and humidity
    arduino = serial.Serial('/dev/cu.usbmodem14301', 9600)
    #opto_vec=np.zeros([np.int32(record_time*samp_rate)])
    #print('Established serial connection to Arduino')


#%%
# -------------------------------------------------------------
# Camera Setup
# -------------------------------------------------------------
cam0 = None
if acquire_images:
    print('Searching for camera...')
    # try PvAPI
    cameras = []
    pvapi_retries = 50
    # get the camera list
    print('Connecting to camera...')
    context0 = Context()
    n = 0
    # Let it have a few tries in case the camera is waking up
    while cam0 is None and n < pvapi_retries:
        try:
            cameras = context0.cameras
            print("Camera IDs:\n", [int(str(cam_id[0]), 16) for cam_id in cameras])
            if len(cameras)>0:
                print("Opening camera!")
                cam0 = Camera() #Camera()
            n += 1
            print('\rsearching...')
            time.sleep(0.5)
        except Exception as e:
            # print("%s" % e)
            cam0 = None
print("Bound to PvAPI camera (name: %s, uid: %s)" % (cam0.model, cam0.guid))

#%% TODO:  set these values manually
#those can be automated, the other are manual
try:
    cam0.brightness.mode = 'auto'
    cam0.exposure.mode = 'auto'
    cam0.white_balance.mode = 'auto'
except AttributeError: # thrown if the camera misses one of the features
    pass

#%%
# Choose Format_7 mode
# See:  ./pydc1394/dc1394.py -- video_mode_vals

print(cam0.modes)
mode_num = 0
cam0.mode = cam0.modes[mode_num] # this is what Nathan uses
# mode_dict = object_fields_dict(cam0.modes[mode_num])
# mode_dict
# mode_dict0:
# mode_id:  88
#   'name': 'FORMAT7_0',
#   'image_size': (1920, 1080),
#   'image_position': (80, 236),
#   'packet_parameters': (260, 15860),
#   'roi': ((1920, 1080), (80, 236), 'RAW8', 15860),

# mode_dict1
# mode_id:  92
#   'name': 'FORMAT7_4',
#   'image_size': (960, 540),
#   'image_position': (40, 118),
#   'roi': ((960, 540), (40, 118), 'RAW8', 3944),
#   'packet_parameters': (68, 3944)
 
# mode_dict2
# mode_id: 95
#   'name': 'FORMAT7_7'
#   image_size: (2080, 1552)
#   packet_params: (52, 6084)
#   image_position: (0, 0)
#   roi: ((2080, 1552), (0, 0), 'RAW8', 6084)


#%%
#Change position to 0,0 (we don't want any offset)
image_pos = (0, 0)
cam0.mode.image_position = image_pos

#To change resolution of acquisition
image_size = (960, 776) #(1080,1080)
cam0.mode.image_size = image_size

#for feat in cam0.features:
#    print("%s (cam0): %s" % (feat,cam0.__getattribute__(feat).value))

#%%
caminfo_fpath = os.path.join(dst_dir, 'caminfo.json')
save_camera_info(cam0, caminfo_fpath)

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
    time_outfile.write('frame_number\tframe_id\tsync_in1\tsync_in2\ttime_stamp\n')

    currdict = im_queue.get()
    while currdict is not None:
        time_outfile.write('%i\t%i\t%i\t%i\t%s\n' % (currdict['frame_count'], currdict['frame_id'], currdict['sync_in1'], currdict['sync_in2'],currdict['time_stamp']))

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

nframes = 0
frame_accumulator = 0
t = 0
last_t = None

report_period = 20 # frames

#Capture images and save them
record_time = 2. # in sec.
samp_rate = 1./frame_rate
time_vec=np.zeros([np.int32(record_time/samp_rate)])

if acquire_images:
    #OPEN STREAM
    #camera.capture_start()
    #camera.queue_frame()
    cam0.start_capture()
    cam0.flush()
    cam0.start_video()
    #cam0.start_one_shot()
    #orig_time = time.time()

#WAIT FOR ACQUISITION START TRIGGER
#print('Waiting for trigger to begin acquisition...')
#while 1:
#    im_array,meta  = camera.capture_wait()
#    if im_array is not None:
#        start_time=time.time()
#        if save_images:
#            fdict = dict()
#            fdict['im_array'] = im_array
#            fdict['frame_count'] = nframes
#            fdict['sync_in1'] = meta['s1']
#            fdict['sync_in2'] = meta['s2']
#            fdict['time_stamp'] = float(0)
#        camera.queue_frame()
#        break
#print('Trigger received')
#
#SAVE FRAMES UNTIL ARDUINO SIGNALS TO STOP
print('Beginning camera acquisition...')
#opto_counter = 0 #initalize opto_counter
# send trigger
if send_trigger:
    string_to_send = "<{}>".format("1")
    byte_string = str.encode(string_to_send)
    arduino.write(byte_string)

nframes=0
start_time = time.time()
last_t = start_time
now=start_time
#while (1):
while time.time()-start_time < record_time:
    #print('hi')
    if acquire_images:
        #for i in range(np.int32(record_time/samp_rate)):
        #target_time = orig_time+samp_rate*i
        #print(time.time()-last_t)
        n=0
        while (time.time()-now) < samp_rate: #target_time:
            #print('Frame %i: %.3f' % (nframes, time.time()-last_t)
            time.sleep(0.0001)
            n+=1
            #print(n)
        now = time.time()
        currt = now-start_time
        #cam0.start_one_shot()
        curr_frame = cam0.dequeue()
        im_array = Image.fromarray(curr_frame.copy())
        #im_array,meta  = camera.capture_wait() 
        #camera.queue_frame()
        #print('--- frame_id:%i, %.3f' % (curr_frame.frame_id, currt))
        if save_images:
            fdict = dict()
            fdict['im_array'] = im_array #curr_frame #im_array
            fdict['frame_count'] = nframes
            fdict['frame_id'] = int(curr_frame.frame_id)
            fdict['sync_in1'] = 0 #meta['s1']
            fdict['sync_in2'] = 0 #meta['s2']
            fdict['time_stamp'] = currt #- start_time
            im_queue.put(fdict)
            #stop saving frames when syncin2 level goes to 0
            #if int(meta['s2'])<1:
            #    break

        #temp_image = Image.fromarray(curr_frame.copy())
        #time_vec[i] = time.time()
        #curr_frame.enqueue()
        #send signal to Arduino
    #    opto_vec[i] = np.multiply(optoBool, 1)
    #    opto_counter += 1
    #    if opto_counter > (opto_time)/samp_rate:
    #        if optoBool*(optoColor=='Red'):
    #            string_to_send = "<{}>".format("2")
    #            byte_string = str.encode(string_to_send)
    #            arduino.write(byte_string)
    #        elif optoBool*(optoColor=='Green'):
    #            string_to_send = "<{}>".format("3")
    #            byte_string = str.encode(string_to_send)
    #            arduino.write(byte_string)
    #        else:
    #            string_to_send = "<{}>".format("1")
    #            byte_string = str.encode(string_to_send)
    #            arduino.write(byte_string)
    #        print(string_to_send)
    #        opto_counter = 0
    #        optoBool = not optoBool #switch opto boolean
    #
        #save_name = str.format('{}/00000{}.bmp', frames_dir, format(nframes))
        #im_array.save(save_name)
        #print(save_name)

        nframes += 1

        if nframes % report_period == 0:
            if last_t is not None:
                print('avg frame rate: %f ' % (report_period / (currt - last_t)))
            last_t=currt
        #print('done')
        curr_frame.enqueue()

print(str.format('total recording time: {} min',(time.time()-start_time)/60))

#%%

print('Acquisition Finished!')
#output performance
acq_duration=time.time()-start_time
print('Total Time: '+str(acq_duration))
expected_frames=int(np.floor(np.around(acq_duration,2)/frame_period))
print('Actual Frame Count = '+str(nframes))
print('Expected Frame Count = '+str(expected_frames))

# write performance to file
performance_file = open(performance_fpath,'w+')
performance_file.write('frame_rate\tframe_period\tacq_duration\tframe_count\texpected_frame_count\tmissingFrames\n')
performance_file.write('%10.4f\t%10.4f\t%10.4f\t%i\t%i\t%i\n'%\
    (frame_rate, frame_period, acq_duration, nframes, expected_frames, expected_frames-nframes))
performance_file.close()

if acquire_images:
    #camera.capture_end()
    #camera.close()
    cam0.stop_capture()
    #cam0.stop_one_shot()
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
if send_trigger:
    string_to_send = "<{}>".format("1")
    byte_string = str.encode(string_to_send)
    arduino.write(byte_string)



print("***** Done! ******")
print('Data saved to: %s' % dst_dir)


# %%
