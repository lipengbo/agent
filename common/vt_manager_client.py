#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:agentclient.py
# Date:Sat Oct 05 18:13:35 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from xmlrpcclient import get_rpc_client
from etc import config


class VTClient(object):
    def __init__(self, ip=config.vt_manager_ip):
        self.client = get_rpc_client(ip, config.vt_manager_port)

    def schedul(self, vcpu, mem, disk, hostlist):
        return self.client.schedul(vcpu, mem, disk, hostlist)
