#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:logging.py
# Date:Thu May 23 10:08:22 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import logging
import logging.config
from etc import config
logging.config.dictConfig(config.LOGGING)


def getLogger(name):
    return logging.getLogger(name)
