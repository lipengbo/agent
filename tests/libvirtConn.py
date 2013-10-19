#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:libvirtConn.py
# Date:Sat Oct 19 15:18:15 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from virt.connection import LibvirtConnection


def test_conn():
    while True:
        conn = LibvirtConnection()._get_connection()
        domain = conn.lookupByName('vm2')
        print domain
