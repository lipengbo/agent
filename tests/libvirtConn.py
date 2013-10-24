#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:libvirtConn.py
# Date:Sat Oct 19 15:18:15 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from virt.libvirtConn import LibvirtConnection
import threading


def conn(str):
    count = 0
    while True:
        try:
            conn = LibvirtConnection()._connect('qemu:///system')
            domain = conn.lookupByName('vm1')
            if count % 100 == 0:
                count = 0
                print str
            count += 1
            print domain.info()
        except:
            print 'error'


def test_conn():
    for i in xrange(10):
        args_for_print = str(i) * 120
        t = threading.Thread(target=conn, args=(args_for_print,))
        t.start()
