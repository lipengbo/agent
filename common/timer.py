#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:timer.py
# Date:Sun Jul 07 18:01:06 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
import traceback
import time
import threading
import log as logging
LOG = logging.getLogger("agent")


class Fork_Timer(object):

    def __init__(self, target, args, interval):
        super(Fork_Timer, self).__init__()
        self.target = target
        self.args = args
        self.interval = interval
        self.thread_stop = False

    def __do(self):
        try:
            self.target(*self.args)
        except:
            LOG.error(traceback.print_exc())
            time.sleep(int(self.interval) * 5)

    def start(self):
        pid = os.fork()
        while pid and (not self.thread_stop):
            self.__do()
            time.sleep(int(self.interval))

    def stop(self):
        self.thread_stop = True


class Timer(threading.Thread):

    def __init__(self, target, args, interval, set_daemon=True):
        super(Timer, self).__init__()
        self.setDaemon(set_daemon)
        self.target = target
        self.args = args
        self.interval = interval
        self.thread_stop = False

    def __do(self):
        try:
            self.target(*self.args)
        except:
            LOG.error(traceback.print_exc())
            time.sleep(int(self.interval) * 5)

    def run(self):
        while not self.thread_stop:
            self.__do()
            time.sleep(int(self.interval))

    def stop(self):
        self.thread_stop = True
