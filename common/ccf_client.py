#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:agentclient.py
# Date:Sat Oct 05 18:13:35 CST 2013
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


def get_rpc_client():
    t = TimeoutTransport()
    t.set_timeout(config.rpc_connection_timeout)
    return xmlrpclib.ServerProxy("http://%s:%s/xmlrpc/" % (config.ccf_ip, config.ccf_port), allow_none=True, transport=t)


class CCFClient(object):

    def set_domain_state(self, vname, state):
        client = get_rpc_client()
        return client.set_domain_state(vname, state)
