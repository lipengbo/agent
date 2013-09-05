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
from service.dhcp import DHCPService
from etc import config
from libs import excutils
from libs import log as logging
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
    if config.dhcp_service:
        service = server.Site(DHCPService())
        reactor.listenTCP(config.dhcp_service_port, service)
    if config.gateway_service:
        start_gateway_service()
    if config.nat_service:
        start_nat_service()
    try:
        reactor.run()
    except Exception:
        LOG.error(traceback.print_exc())


def set_host_perf():
    excutils.execute('sysctl -w net.ipv4.tcp_tw_reuse=1')
    excutils.execute('sysctl -w net.ipv4.tcp_tw_recycle=1')
    excutils.execute('sysctl -w net.ipv4.tcp_timestamps=1')


def start_gateway_service():
    from service.gateway import GatewayService
    service = server.Site(GatewayService())
    print 'gateway service starting...'
    reactor.listenTCP(config.gateway_service_port, service)
    print 'gateway service started'


def start_nat_service():
    from service.nat import NatService
    service = server.Site(NatService())
    print 'nat service starting...'
    reactor.listenTCP(config.nat_service_port, service)
    print 'nat service started'


def recover_gw_config():
    try:
        with open(excutils.IP_BAK_FILE, 'r') as ipFile:
            content = ipFile.readlines()
        for cmd in content:
            excutils._execute(cmd)
    except:
        LOG.error(traceback.print_exc())


def recover_nat_config():
    try:
        cmd = 'iptables-restore < %s' % excutils.IPTABLES_BAK_FILE
        excutils._execute(cmd)
    except:
        LOG.error(traceback.print_exc())


if __name__ == '__main__':
    set_host_perf()
    start_service()
    recover_gw_config()
    recover_nat_config()
