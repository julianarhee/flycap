#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   camera_utils.py
@Time    :   2021/12/06 17:04:34
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''


from simple_pyspin import Camera

def create_default_camera(framerate=97.0, width=1280, height=960, gamma=1.5):
#    framerate = 97.0 
#    width = 1280
#    height = 960
#    gamma = 1.5
    framerate = min([framerate, 97.])
#%% Initialize camera
    cam = Camera() 
    cam.init() 

#%%
    cam.VideoMode = 'Mode8'
    cam.PixelFormat = 'Mono8'
    cam.Width = width
    cam.Height = height
    # center frame
    cam.OffsetX = (cam.SensorWidth - cam.Width) //4
    cam.OffsetY = (cam.SensorHeight - cam.Height) //4
    print("Camera BB. x: {}, {}, y: {}, {} (Image is {}x{})".format(\
        cam.OffsetX, cam.OffsetX+cam.Width, cam.OffsetY, cam.OffsetY+cam.Height, cam.Width, cam.Height))

    # Frame rate
    # --------------------------------------------------------------------
    # To change the frame rate, we need to enable manual control
    cam.AcquisitionFrameRateAuto = 'Off'
    cam.AcquisitionFrameRateEnabled = True
    cam.AcquisitionFrameRate = framerate

    # Gain 
    # --------------------------------------------------------------------
    # To control the exposure settings, we need to turn off auto
    cam.GainAuto = 'Off'
    # Turn off gain (or, Set the gain to 20 dB or the maximum of the camera.)
    gain = min(0, cam.get_info('Gain')['min'])
    print("Setting gain to %.1f dB" % gain)
    cam.Gain = gain
    cam.ExposureAuto = 'Off'
    cam.ExposureTime = min([(1./framerate)*1E6, 10294.556]) #10000 # microseconds
        
    # Gamma
    # --------------------------------------------------------------------
    # If we want an easily viewable image, turn on gamma correction.
    # NOTE: for scientific image processing, you probably want to
    #    _disable_ gamma correction!
    try:
        cam.GammaEnabled = True
        cam.Gamma = gamma
    except:
        print("Failed to change Gamma correction (not avaiable on some cameras).")


    return cam

