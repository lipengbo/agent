#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:__init__.py
# Date:Fri Sep 13 14:50:28 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
import sys
netaddr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.insert(0, netaddr_path)
from netaddr.core import AddrConversionError, AddrFormatError, \
    NotRegisteredError, ZEROFILL, Z, INET_PTON, P, NOHOST, N

from netaddr.ip import IPAddress, IPNetwork, IPRange, all_matching_cidrs, \
    cidr_abbrev_to_verbose, cidr_exclude, cidr_merge, iprange_to_cidrs, \
    iter_iprange, iter_unique_ips, largest_matching_cidr, \
    smallest_matching_cidr, spanning_cidr

from netaddr.ip.sets import IPSet

from netaddr.ip.glob import IPGlob, cidr_to_glob, glob_to_cidrs, \
    glob_to_iprange, glob_to_iptuple, iprange_to_globs, valid_glob

from netaddr.ip.nmap import valid_nmap_range, iter_nmap_range

from netaddr.ip.rfc1924 import base85_to_ipv6, ipv6_to_base85

from netaddr.eui import EUI, IAB, OUI

from netaddr.strategy.ipv4 import valid_str as valid_ipv4

from netaddr.strategy.ipv6 import valid_str as valid_ipv6, ipv6_compact, \
    ipv6_full, ipv6_verbose

from netaddr.strategy.eui48 import mac_eui48, mac_unix, mac_cisco, \
    mac_bare, mac_pgsql, valid_str as valid_mac

__all__ = [
    #   Constants.
    'ZEROFILL', 'Z', 'INET_PTON', 'P', 'NOHOST', 'N',

    #   Custom Exceptions.
    'AddrConversionError', 'AddrFormatError', 'NotRegisteredError',

    #   IP classes.
    'IPAddress', 'IPNetwork', 'IPRange', 'IPSet',

    #   IPv6 dialect classes.
    'ipv6_compact', 'ipv6_full', 'ipv6_verbose',

    #   IP functions and generators.
    'all_matching_cidrs', 'cidr_abbrev_to_verbose', 'cidr_exclude',
    'cidr_merge', 'iprange_to_cidrs', 'iter_iprange', 'iter_unique_ips',
    'largest_matching_cidr', 'smallest_matching_cidr', 'spanning_cidr',

    #   IP globbing class.
    'IPGlob',

    #   IP globbing functions.
    'cidr_to_glob', 'glob_to_cidrs', 'glob_to_iprange', 'glob_to_iptuple',
    'iprange_to_globs',

    #   IEEE EUI classes.
    'EUI', 'IAB', 'OUI',

    #   EUI-48 (MAC) dialect classes.
    'mac_bare', 'mac_cisco', 'mac_eui48', 'mac_pgsql', 'mac_unix',

    #   Validation functions.
    'valid_ipv4', 'valid_ipv6', 'valid_glob', 'valid_mac',

    #   nmap-style range functions.
    'valid_nmap_range', 'iter_nmap_range',

    #   RFC 1924 functions.
    'base85_to_ipv6', 'ipv6_to_base85',
]


class Network(IPNetwork):

    def subnet(self, ipcount, *args, **kwargs):
        if ipcount == 64:
            prefixlen = 26
        elif ipcount == 32:
            prefixlen = 27
        elif ipcount == 16:
            prefixlen = 28
        elif ipcount == 8:
            prefixlen = 29
        else:
            prefixlen = self.prefixlen
        return super(Network, self).subnet(prefixlen, *args, **kwargs)

    def get_subnet(self, ipcount, index):
        if ipcount == 64:
            prefixlen = 26
        elif ipcount == 32:
            prefixlen = 27
        elif ipcount == 16:
            prefixlen = 28
        elif ipcount == 8:
            prefixlen = 29
        else:
            prefixlen = self.prefixlen
        width = self._module.width
        max_subnets = (1 << (width - self.prefixlen)) // (1 << (width - prefixlen))
        if index >= max_subnets:
            raise ValueError('Index outside of current IP subnet boundary!')
        base_subnet = self._module.int_to_str(self.first)
        subnet = self.__class__('%s/%d' % (base_subnet, prefixlen), self._module.version)
        subnet.value += (subnet.size * index)
        subnet.prefixlen = prefixlen
        return subnet

    def get_supernet(self, superprefix):
        if not 0 <= superprefix <= self._module.width:
            raise ValueError('CIDR prefix /%d invalid for IPv%d!' % (superprefix, self._module.version))
        supernet = self.cidr
        supernet._prefixlen = superprefix
        return supernet

    def get_previous(self, superprefix, step=1):
        ip_previous = self.previous(step)
        if self.get_supernet(superprefix) in ip_previous.supernet():
            return ip_previous
        raise StopIteration

    def get_next(self, superprefix, step=1):
        ip_next = self.next(step)
        if self.get_supernet(superprefix) in ip_next.supernet():
            return ip_next
        raise StopIteration

    def get_host(self, index):
        if 0 <= index <= self.last - self.first - 2:
            return IPAddress(self.first + 1 + index, self._module.version)
        else:
            raise StopIteration

    def get_first_host(self):
        return str(IPAddress(self.first))


def generate_mac_address(ip):
    """Generate an Ethernet MAC address."""
    base_bin = EUI('fa:16:00:00:00:00').value
    return str(EUI(base_bin | IPAddress(ip).value)).replace('-', ':')


def clean_ip(ip_str):
    return ip_str.partition('/')[0]
