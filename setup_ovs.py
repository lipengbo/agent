#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:setup_ovs.py
# Date:Wed Aug 28 09:38:04 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import sys
from common import utils
from ovs import vswitch
import getopt


def usage():
    print "python setup_ovs.py --out_if=eth0 --out_br=br100 --ip=192.168.5.9 --netmask=255.255.255.0 --gateway=192.168.5.1"


def parse_parameter(argv):
    out_if = None
    out_br = None
    local_ip = None
    netmask = None
    gateway = None
    try:
        opts, args = getopt.getopt(argv, 'h:', ['out_if=', 'out_br=', 'ip=', 'netmask=', 'gateway='])
        if len(opts) < 5:
            usage()
            sys.exit(1)
        for opt, value in opts:
            if opt in ('-h', '--help'):
                usage()
                sys.exit(1)
            elif opt == '--out_if':
                out_if = value
            elif opt == '--out_br':
                out_br = value
            elif opt == '--ip':
                local_ip = value
            elif opt == '--netmask':
                netmask = value
            elif opt == '--gateway':
                gateway = value
            else:
                print 'Unhandled options'
                sys.exit(3)
        return out_if, out_br, local_ip, netmask, gateway
    except getopt.GetoptError:
        usage()
        sys.exit(2)


def genarate_dpid(out_if):
    out, err = utils.execute("ip link show %s | grep -i link/ether |awk '{print $2}'" % out_if)
    dpid = "ffff" + "".join(out.strip().split(":"))
    return dpid


def setup_ovs(out_if, out_br, local_ip, netmask, gateway):
    result = vswitch.ovs_vsctl_add_bridge(out_br)
    print result
    result = vswitch.ovs_set_bridge_dpid(out_br, genarate_dpid(out_if))
    print result
    result = vswitch.ovs_vsctl_add_port_to_bridge(out_br, out_if)
    print result
    utils.execute("ifconfig %s 0 up" % out_if)
    utils.execute("ifconfig %s %s netmask %s up" % (out_br, local_ip, netmask))
    out, err = utils.execute("route -n")
    for route in out.splitlines():
        if route.startswith("0.0.0.0"):
            out, err = utils.execute(
                "route del default dev %s" % route.split()[7])
    utils.execute("route add default gw %s" % gateway)


if __name__ == '__main__':
    argv = parse_parameter(sys.argv[1:])
    print argv
    setup_ovs(*argv)
