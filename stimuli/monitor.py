#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:53:33 2021

@author: julianarhee
"""

from psychopy import visual, monitors
import re

if __name__ == '__main__':
    
    print("Enter monitor name to create new calibration: ")
    monitor_name = str(input())
    t = monitors.Monitor(monitor_name)

    screenW = float(input("Enter WIDTH (cm): "))
    t.setWidth(screenW)

    screen_res_str = input("Enter screen size (pix) as screenW,screenH (no spaces): ")
    w, h = screen_res_str.split(',')
    screen_size_pix = [int(w), int(h)] 
    print(screen_size_pix)
    t.setSizePix(screen_size_pix)
    distance = float(input("Distance from eye to monitor (cm)? "))
    t.setDistance(distance)

    t.setCalibDate()

    print("**************************************************************")
    print("Save new calibration file for monitor, %s? [y/n]" % monitor_name)
    print("**************************************************************")
    print("Properties:")
    print("-----------")
    print("screenW (cm): %i " % screenW)
    print("screen size in pixels: %s" % screen_size_pix)
    print("distance (cm): %f " % distance)

    agree = str(input("Save settings? y/n"))
    if re.match(r'y', agree): # ~/.psychopy3/monitors
        t.saveMon()

    print(monitors.getAllMonitors())
