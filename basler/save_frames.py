#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   save_frames.py
@Time    :   2022/01/27 16:29:03
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''

import sys
import os
import time
import cv2
import errno
import optparse

from queue import Queue
import numpy as np
import multiprocessing as mp

from pypylon import pylon
from pypylon import genicam


def find_cameras():
    '''Find connected cameras'''
    tl_factory = pylon.TlFactory.GetInstance() # create transport layer
    devices = tl_factory.EnumerateDevices()    # enumerate devices it has access to
    for device in devices:
        print(device.GetFriendlyName())
        
    return

def connect_to_camera(connect_retries=50):
    
    print('Searching for camera...')
    camera = None
    # get the camera list 
    print('Connecting to camera...')   
    n = 0
    while camera is None and n < connect_retries:
        try:
            #tl_factory = pylon.TlFactory.GetInstance() # create transport layer
            #camera = pylon.InstantCamer() # create instant cam object 
            #camera.Attach(tl_factory.CreateFirstDevice()) # attach wrapper InstantCam to device
            camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
            print(camera)
            #time.sleep(0.5)
            #camera.Open()
            #print("Bound to device:" % (camera.GetDeviceInfo().GetModelName()))

        except Exception as e:
            print('.')
            time.sleep(0.1)
            camera = None
            n += 1

    if camera is None:
        print("no camera")
        
    return camera


#%%

camera = connect_to_camera()

frame_rate=10.0
exposure_time=16.67
enable_framerate=True

#%%
def set_configs(camera, frame_rate=20., exposure_time_ms=16.67, 
                acquisition_line='Line3', enable_framerate=True):
#%%
    if camera is None:
        print("Could not load camera")
        exit()
    else:
        camera.Open() # open camera
        print("Bound to device: %s" % (camera.GetDeviceInfo().GetModelName()))

    camera.AcquisitionFrameRateEnable = enable_framerate
    camera.AcquisitionFrameRate = frame_rate
    if enable_framerate:
        camera.AcquisitionMode.SetValue('Continuous')
        print("Set acquisition frame rate: %.2f Hz" % camera.AcquisitionFrameRate())
        for trigger_type in ['FrameStart', 'FrameBurstStart']:
            camera.TriggerSelector = trigger_type
            camera.TriggerMode = "Off"
    else: 
        # Set  trigger
        camera.TriggerSelector = "FrameStart"
        camera.TriggerMode = "On"
    
#    camera.TriggerSource.SetValue(acquisition_line)
#    #camera.TriggerSelector.SetValue('AcquisitionStart')
#    camera.TriggerActivation = 'RisingEdge'
#
#    # Set IO lines:
#    camera.LineSelector.SetValue(acquisition_line) # select GPIO 1
#    camera.LineMode.SetValue('Input')     # Set as input
#    #camera.LineStatus.SetValue(False)
#    
#    # Output:
#    camera.LineSelector.SetValue('Line4')
#    camera.LineMode.SetValue('Output')
#    camera.LineSource.SetValue('UserOutput3') # Set source signal to User Output 1
#    camera.UserOutputSelector.SetValue('UserOutput3')
#    camera.UserOutputValue.SetValue(False)       
# 
    # Set image format:
    camera.ShutterMode.SetValue('GlobalResetRelease')
    camera.ExposureAuto.SetValue('Off')
    exposure_time_us = exposure_time_ms*1E3
    camera.ExposureTime.SetValue(exposure_time_us)
#    camera.Width.SetValue(960)
#    camera.Height.SetValue(600)
#    camera.BinningHorizontalMode.SetValue('Sum')
#    camera.BinningHorizontal.SetValue(2)
#    camera.BinningVerticalMode.SetValue('Sum')
#    camera.BinningVertical.SetValue(2)
#    camera.PixelFormat.SetValue('Mono8')
#    camera.ExposureMode.SetValue('Timed')
#    camera.ExposureTime.SetValue(40000)
#
    try:
        actual_framerate = camera.ResultingFrameRate.GetValue()
        assert camera.AcquisitionFrameRate() <= camera.ResultingFrameRate(), "Unable to acquieve desired frame rate (%.2f Hz)" % float(camera.AcquisitionFrameRate.GetValue())
    except AssertionError:
        camera.AcquisitionFrameRate.SetValue(float(camera.ResultingFrameRate.GetValue()))
        print("Set acquisition rate to: %.2f" % camera.AcquisitionFrameRate())

    return camera


# ############################################
# Camera functions
# ############################################

class SampleImageEventHandler(pylon.ImageEventHandler):
    def OnImageGrabbed(self, camera, grabResult):
        #print("CSampleImageEventHandler::OnImageGrabbed called.")
        camera.UserOutputValue.SetValue(True)
        #camera.UserOutputValue.SetValue(True)


def extract_options(options):

    parser = optparse.OptionParser()
    parser.add_option('--dst-dir', action="store", dest="dst_dir", default="/home/julianarhee/tmp", help="out path directory [default: /home/julianarhee/tmp]")
    parser.add_option('--output-format', action="store", dest="output_format", type="choice", choices=['png', 'npz'], default='png', help="out file format, png or npz [default: png]")
    parser.add_option('--save', action='store_true', dest='save_images', default=False, help='Flag to save images to disk.')
    parser.add_option('--no-camera', action='store_false', dest='acquire_images', default=True, help='Flag to set no camera.')

    parser.add_option('--basename', action="store", dest="basename", default="default_frame", help="basename for saved files")

    parser.add_option('--write-process', action="store_true", dest="save_in_separate_process", default=True, help="spawn process for disk-writer [default: True]")
    parser.add_option('--write-thread', action="store_false", dest="save_in_separate_process", help="spawn threads for disk-writer")
    parser.add_option('--frame-rate', action="store", dest="frame_rate", help="requested frame rate", type="float", default=10.0)
    parser.add_option('--port', action="store", dest="port", help="port for arduino (default: /dev/ttyUSB0)", default='/dev/ttyUSB0')
    parser.add_option('--disable', action='store_false', dest='enable_framerate', default=True, help='Flag to disable acquisition frame rate setting.')

    (options, args) = parser.parse_args()

    return options

if __name__ == '__main__':

    optsE = extract_options(sys.argv[1:])
    
    # Save settings
    dst_dir = optsE.dst_dir
    basename = optsE.basename
    acquire_images = optsE.acquire_images  
    save_images = optsE.save_images
    
    # Make the output path if it doesn't already exist
    output_dir = os.path.join(dst_dir, basename)
    frame_write_dir = os.path.join(output_dir, 'frames')
    try:
        os.makedirs(frame_write_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
        pass
   
    # Create streaming window 
    cv2.namedWindow('cam_window')
    r = np.random.rand(100,100)
    cv2.imshow('cam_window', r)
    time.sleep(1.0)

    # -------------------------------------------------------------
    # Camera Setup
    # ------------------------------------------------------------     
    frame_rate = optsE.frame_rate  
    enable_framerate = optsE.enable_framerate
    #acquisition_line = 'Line3'
    camera = None
    if acquire_images:
        try:
            camera = connect_to_camera()
            camera = set_configs(camera, frame_rate=frame_rate, enable_framerate=enable_framerate,
                                 #acquisition_line=acquisition_line,
                                 )
        except Exception as e:
            print(e)
            print("No camera")
                
    # Attach event handlers:
    camera.RegisterImageEventHandler(SampleImageEventHandler(), pylon.RegistrationMode_Append, pylon.Cleanup_Delete)

    time.sleep(1)
    print("Camera ready!")

    # --------------------------------------------------------------
    # Setup acquisition
    # --------------------------------------------------------------
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) #GrabStrategy_OneByOne)
    # converting to opencv bgr format  
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
    
    #camera.LineSelector.SetValue(acquisition_line) 
    sync_line = camera.LineSelector.GetValue()
    sync_state = camera.LineStatus.GetValue()
    #print("Waiting for Acquisition Start trigger...", sync_state)
    while sync_state is False: 
        print("[%s] trigger" % sync_line, sync_state)
        sync_state = camera.LineStatus.GetValue()
    print("... ... Trigger received!")
    camera.AcquisitionStart.Execute()
 
 
    # -------------------------------------------------------------
    # Set up a thread to write stuff to disk
    # -------------------------------------------------------------
    if save_images:
        im_queue = mp.Queue() 
 
    # Start acquiring
    last_t=None
    nframes=0
    timeout_time=100 # 
    report_period=60
    print('Beginning imaging [Hit ESC to quit]...')
    while camera.IsGrabbing():
        t = time.time()
                
        #while camera.IsGrabbing():
        # Grab a frame:
        #camera.WaitForFrameTriggerReady(100)
        res = camera.RetrieveResult(timeout_time, pylon.TimeoutHandling_ThrowException)
        if res and res.GrabSucceeded():
            # Access img data:
            im_native = res.Array
            im_to_show = converter.Convert(res)
            im_array = im_to_show.GetArray()
            frame_state = camera.UserOutputValue.GetValue()
            meta = {'tstamp': res.TimeStamp, 
                    'ID': res.ID,
                    'number': res.ImageNumber,
                    'acq_trigger': sync_state,
                    'frame_trigger': frame_state}
            if save_images:
                im_queue.put((im_native, meta))
            nframes += 1
            res.Release()

        # Show image:
        cv2.imshow('cam_window', im_array)
        camera.UserOutputValue.SetValue(False)

        # Break out of the while loop if ESC registered
        key = cv2.waitKey(1)
        sync_state = camera.LineStatus.GetValue()
        if key == 27 or sync_state is False: # ESC
            break
        #res.Release()

        if nframes % report_period == 0:
            if last_t is not None:
                print('avg frame rate: %f [Hit ESC to quit]' % (report_period / (t - last_t)))
                print('ID: %i, nframes: %i, %s' % (meta['ID'], nframes, meta['tstamp']) )
            last_t = t

    camera.AcquisitionStop.Execute()
    #camera.AcquisitionStart.Execute()

    # Relase the resource:
    camera.UserOutputValue.SetValue(False) 
    camera.StopGrabbing()
    cv2.destroyAllWindows()

    camera.Close() 


   
    