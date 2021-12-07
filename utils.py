#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   utils.py
@Time    :   2021/12/06 18:00:41
@Author  :   julianarhee 
@Contact :   juliana.rhee@gmail.com
'''

import re

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]
