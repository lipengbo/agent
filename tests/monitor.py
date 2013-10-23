#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:monitor.py
# Date:Wed Oct 23 13:51:53 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from service.monitor import DomainMonitor
from service.monitor import HostMonitor
import time


def get_domain_status():
    dom_monitor = DomainMonitor('vm1')
    print dom_monitor.get_status()
    time.sleep(1)
    dom_monitor = DomainMonitor('test')
    print dom_monitor.get_status()


def get_host_status():
    host = HostMonitor()
    print host.get_status()


def get_host_info():
    host = HostMonitor()
    print host.get_info()
