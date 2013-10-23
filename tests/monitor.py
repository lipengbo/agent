#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:monitor.py
# Date:Wed Oct 23 13:51:53 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from service.monitor import MonitorService


monitor_service = MonitorService()


def get_domain_status():
    print monitor_service.xmlrpc_get_domain_status('vm1')


def get_host_status():
    print monitor_service.xmlrpc_get_host_status()


def get_host_info():
    print monitor_service.xmlrpc_get_host_info()
