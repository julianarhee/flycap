#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   viewer2.py
@Time    :   2021/12/06 13:09:45
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''

#%%
import sys
import cv2
import numpy as np  
import logging
import time
#from point_grey import Camera

from simple_pyspin import Camera
import camera_utils as cutils


#To log to file:
#logging.basicConfig(level = logging.DEBUG, filename = 'logs/pgcam.log', filemode = 'w') #set to 'a' to append
#To log to stdout:
logging.basicConfig(level = logging.INFO)  #set to DEBUG if you want way too much info

#%%
#system = PySpin.System.GetInstance()
#
#cam = system.GetCameras()[0]
#cam.Init()
#nodemap = cam.GetNodeMap()
#
# nodemap


#with Camera() as cam:
#    print(cam.Width)

#%%
if __name__ == "__main__":
    """ 
    Test PySpin api/SpinnakerCamera() using opencv.
    grasshopper maxfov/fps: 2048 x 2048/90
    chameleon maxfov: 1288x968/30
    """
 
#    framerate = 97.0 
#    width = 1280
#    height = 960
#    gamma = 1.5
#
##%% Initialize camera
#    cam = Camera() 
#    cam.init() 
#
##%%
#    cam.VideoMode = 'Mode8'
#    cam.PixelFormat = 'Mono8'
#    cam.Width = width
#    cam.Height = height
#    # center frame
#    cam.OffsetX = (cam.SensorWidth - cam.Width) //4
#    cam.OffsetY = (cam.SensorHeight - cam.Height) //4
#    print("Camera BB. x: {}, {}, y: {}, {} (Image is {}x{})".format(\
#        cam.OffsetX, cam.OffsetX+cam.Width, cam.OffsetY, cam.OffsetY+cam.Height, cam.Width, cam.Height))
#
#    # Frame rate
#    # --------------------------------------------------------------------
#    # To change the frame rate, we need to enable manual control
#    cam.AcquisitionFrameRateAuto = 'Off'
#    cam.AcquisitionFrameRateEnabled = True
#    cam.AcquisitionFrameRate = framerate
#
#    # Gain 
#    # --------------------------------------------------------------------
#    # To control the exposure settings, we need to turn off auto
#    cam.GainAuto = 'Off'
#    # Turn off gain (or, Set the gain to 20 dB or the maximum of the camera.)
#    gain = min(0, cam.get_info('Gain')['min'])
#    print("Setting gain to %.1f dB" % gain)
#    cam.Gain = gain
#    cam.ExposureAuto = 'Off'
#    cam.ExposureTime = min([(1./framerate)*1E6, 10294.556]) #10000 # microseconds
#        
#    # Gamma
#    # --------------------------------------------------------------------
#    # If we want an easily viewable image, turn on gamma correction.
#    # NOTE: for scientific image processing, you probably want to
#    #    _disable_ gamma correction!
#    try:
#        cam.GammaEnabled = True
#        cam.Gamma = gamma
#    except:
#        print("Failed to change Gamma correction (not avaiable on some cameras).")
#
    framerate=100.0
    cam = cutils.create_default_camera(framerate=framerate)
#%%
    logging.info("\n**Testing PgCam()**".format(framerate))
    cv2.namedWindow("PgCam", cv2.WINDOW_NORMAL)
    #pgCam = Camera(roi, frame_rate, gain, exposure_ms)
    #pgCam.open_camera()
    cam.start()
    while True:
        image = cam.get_array() #pgCam.read()
        cv2.imshow("PgCam", image)
        key = cv2.waitKey(1)  
        if key == 27: #escape key
            logging.info("Streaming stopped")
            cv2.destroyAllWindows()
            #pgCam.release()
            cam.close()
            break
 

#%%


#cam.close()

