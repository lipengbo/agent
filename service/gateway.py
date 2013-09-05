#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:gateway.py
# Date:Wed Sep 04 18:29:00 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from libs import excutils as excutils
from libs import log as logging
from libs import IPy
from etc import config
from ovs import vswitch
LOG = logging.getLogger("agent.libs.excutils")


class GatewayHandler(object):

    def __init__(self):
        pass

    def start_gateway_service(self, gwip, netaddr, outif=None):
        if outif is None:
            outif = self.__prepare_link(gwip)
        return self.__add_address_to_interface(outif, gwip, netaddr)
        #     return self.__add_network_to_route_table(outif, netaddr)
        # return False

    def stop_gateway_service(self, gwip, netaddr, outif=None):
        if outif is None:
            outif = self.__prepare_link(gwip)
        if self.__del_network_from_route_table(outif, netaddr):
            return self.__del_address_from_interface(outif, gwip, netaddr)
        return False

    def __add_address_to_interface(self, outif, gwip, netaddr):
        # ip addr add 192.168.2.254/24 dev eth0
        try:
            result, error = excutils.execute(
                'sudo ip addr add %s dev %s' % (gwip, outif))
            result, error = excutils.execute(
                'sudo iptables -t nat -A POSTROUTING -s %s -j MASQUERADE' % netaddr)
            if not error:
                return True
            return False
        except Exception as e:
            LOG.error(str(e))
            return False

    def __del_address_from_interface(self, outif, gwip, netaddr):
        # ip addr del 192.168.2.254/24 dev eth0
        try:
            result, error = excutils.execute(
                'sudo ip addr del %s dev %s' % (gwip, outif))
            result, error = excutils.execute(
                'sudo iptables -t nat -D POSTROUTING -s %s -j MASQUERADE' % netaddr)
            if not error:
                return True
            else:
                return False
        except Exception as e:
            LOG.error(str(e))
            return False

    def __add_network_to_route_table(self, outif, netaddr):
        # ip route add 192.168.2.0/24 dev eth0
        command = 'sudo ip route add %s dev %s' % (netaddr, outif)
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            return False

    def __del_network_from_route_table(self, outif, netaddr):
        # ip route del 192.168.2.0/24 dev eth0
        command = 'sudo ip route del %s dev %s' % (netaddr, outif)
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            return False

    def __prepare_link(self, gwip):
        fix = IPy.IP(gwip).strDec()
        bridge_port = 'b%s' % fix
        peer_port = 'p%s' % fix
        excutils.execute(['ip', 'link', 'add', bridge_port, 'type', 'veth', 'peer', 'name', peer_port])
        excutils.execute(['ip', 'link', 'set', bridge_port, 'up'])
        excutils.execute(['ip', 'link', 'set', peer_port, 'up'])
        excutils.execute(['ip', 'link', 'set', bridge_port, 'promisc', 'on'])
        excutils.execute(['ip', 'link', 'set', peer_port, 'promisc', 'on'])
        vswitch.ovs_vsctl_add_port_to_bridge(config.out_br, peer_port)
        return peer_port


from twisted.web import xmlrpc


class GatewayService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)

    def render(self, request):
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_start_gateway_service(self, gwip, netaddr, outif=None):
        """
        print "start_gateway_service outif: %s, gwip: %s, netaddr: %s" % (outif, gwip, netaddr)
        return True
        """
        handler = GatewayHandler()
        return handler.start_gateway_service(gwip, netaddr, outif)

    def xmlrpc_stop_gateway_service(self, gwip, netaddr, outif=None):
        """
        print "stop_gateway_service outif: %s, gwip: %s, netaddr: %s" % (outif, gwip, netaddr)
        return True
        """
        handler = GatewayHandler()
        return handler.stop_gateway_service(gwip, netaddr, outif)
