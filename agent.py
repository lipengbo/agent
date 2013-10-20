#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:agent.py
# Date:Sat Jul 06 11:55:55 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import traceback
from twisted.internet import reactor
from twisted.web import server
from service.ovs_service import DeviceCommService
from service.monitor import MonitorService
from service.compute import ComputeService
from etc import config
from common import log as logging
LOG = logging.getLogger("agent.virt")


def start_service():
    if config.compute_service:
        service = server.Site(ComputeService())
        reactor.listenTCP(config.compute_service_port, service)
    if config.ovs_service:
        service = server.Site(DeviceCommService())
        reactor.listenTCP(config.ovs_service_port, service)
    if config.monitor_service:
        service = server.Site(MonitorService())
        reactor.listenTCP(config.monitor_service_port, service)
    try:
        reactor.run()
    except Exception:
        LOG.error(traceback.print_exc())


if __name__ == '__main__':
    start_service()
