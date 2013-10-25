#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:xmlrpcclient.py
# Date:Fri Oct 25 11:16:35 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import xmlrpclib
import httplib
from etc import config


class TimeoutTransport(xmlrpclib.Transport):
    timeout = config.rpc_connection_timeout

    def set_timeout(self, timeout):
        self.timeout = timeout

    def make_connection(self, host):
        h = httplib.HTTPConnection(host, timeout=self.timeout)
        return h


def get_rpc_client(ip, port):
    t = TimeoutTransport()
    t.set_timeout(config.rpc_connection_timeout)
    return xmlrpclib.ServerProxy("http://%s:%s/" % (ip, port), allow_none=True, transport=t)
