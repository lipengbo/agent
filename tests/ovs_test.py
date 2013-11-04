#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:ovs.py
# Date:Mon Nov 04 16:59:59 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from ovs import vswitch


def get_port_bandwidth():
    return vswitch.ovs_get_port_bandwidth('br100')
