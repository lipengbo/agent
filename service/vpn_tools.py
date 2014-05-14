#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:vpn_tools.py
# Date:三  5月 14 14:07:33 CST 2014
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import traceback
from common import utils
from twisted.web import xmlrpc
from common import log as logging
LOG = logging.getLogger("agent")


class VPNService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        self.request = None

    def render(self, request):
        self.request = request
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_add_route(self, net, gw):
        cmd = 'route add -net %s gw %s' % (net, gw)
        result = True
        try:
            utils.execute(cmd)
        except:
            result = False
            LOG.error(traceback.print_exc())
        return result

    def xmlrpc_del_route(self, net, gw):
        cmd = 'route del -net %s gw %s' % (net, gw)
        result = True
        try:
            utils.execute(cmd)
        except:
            result = False
            LOG.error(traceback.print_exc())
        return result
