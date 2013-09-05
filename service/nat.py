#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:nat.py
# Date:Wed Sep 04 18:31:44 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from libs import excutils as excutils
from etc import config


class NatHandler(object):

    def __init__(self):
        pass

    def add_snat(self, private_address, outif=None):
        if outif is None:
            outif = config.gateway_service_bridge
        # iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -j MASQUERADE
        command = 'sudo iptables -t nat -A POSTROUTING -s %s -j MASQUERADE' % private_address
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            return False

    def del_snat(self, private_address, outif=None):
        if outif is None:
            outif = config.gateway_service_bridge
        # iptables -t nat -D POSTROUTING -s 192.168.1.0/24 -j MASQUERADE
        command = 'sudo iptables -t nat -D POSTROUTING -s %s -j MASQUERADE' % private_address
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            return False

    def add_dnat(self, private_address, public_address, outif=None):
        if outif is None:
            outif = config.gateway_service_bridge
        if self.__map_address_for_dnat(private_address, public_address):
            return self.__add_address_to_interface(outif, private_address)
        return False

    def del_dnat(self, private_address, public_address, outif=None):
        if outif is None:
            outif = config.gateway_service_bridge
        if self.__unmap_address_for_dnat(private_address, public_address):
            return self.__del_address_from_interface(outif, private_address)
        return False

    def __map_address_for_dnat(self, private_address, public_address):
        # iptables -t nat -A PREROUTING -d 192.168.1.100 -j DNAT
        # --to-destination 192.168.168.10
        command = 'sudo iptables -t nat -A PREROUTING -d %s -j DNAT --to-destination %s' % (
            public_address, private_address)
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            return False

    def __unmap_address_for_dnat(self, private_address, public_address):
        # iptables -t nat -D PREROUTING -d 192.168.1.100 -j DNAT
        # --to-destination 192.168.168.10
        command = 'sudo iptables -t nat -D PREROUTING -d %s -j DNAT --to-destination %s' % (
            public_address, private_address)
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            print "__unmap_address_for_dnat: %s" % error
            return False

    def __add_address_to_interface(self, outif, addr):
        # ip addr add 192.168.2.254/32 dev eth0
        command = 'sudo ip addr add %s/32 dev %s' % (addr, outif)
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            return False

    def __del_address_from_interface(self, outif, addr):
        # ip addr del 192.168.2.254/32 dev eth0
        command = 'sudo ip addr del %s/32 dev %s' % (addr, outif)
        result, error = excutils.execute(command)
        if not error:
            return True
        else:
            print "__del_address_from_interface: %s" % error
            return False

from twisted.web import xmlrpc


class NatService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)

    def render(self, request):
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_add_snat(self, private_address, outif=None):
        """
        print "add_snat outif: %s, private: %s" % (outif, private_address)
        return True
        """
        handler = NatHandler()
        return handler.add_snat(private_address, outif)

    def xmlrpc_del_snat(self, private_address, outif=None):
        """
        print "del_snat outif: %s, private: %s" % (outif, private_address)
        return True
        """
        handler = NatHandler()
        return handler.del_snat(private_address, outif)

    def xmlrpc_add_dnat(self, private_address, public_address, outif=None):
        """
        print "add_dnat outif: %s, private: %s, public: %s" % (outif,
                                                               private_address,
                                                               public_address)
        return True
        """
        handler = NatHandler()
        return handler.add_dnat(private_address, public_address, outif)

    def xmlrpc_del_dnat(self, private_address, public_address, outif=None):
        """
        print "del_dnat outif: %s, private: %s, public: %s" % (outif,
                                                               private_address,
                                                               public_address)
        return True
        """
        handler = NatHandler()
        return handler.del_dnat(private_address, public_address, outif)
