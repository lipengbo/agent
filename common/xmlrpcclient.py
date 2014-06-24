#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:client.py
# Date:Fri Jul 05 17:38:12 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import xmlrpclib
import httplib
from etc import config


class TimeoutTransport(xmlrpclib.Transport):

    def set_timeout(self, timeout):
        self.timeout = timeout

    def make_connection(self, host):
        h = httplib.HTTPConnection(host, timeout=self.timeout)
        return h


def get_rpc_client(ip, port, timeout=None):
    t = TimeoutTransport()
    if timeout:
        t.set_timeout(timeout)
    else:
        t.set_timeout(config.rpc_connection_timeout)
    return xmlrpclib.ServerProxy("http://%s:%s/" % (ip, port), allow_none=True, transport=t)
