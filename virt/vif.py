#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:vif.py
# Date:Mon Oct 21 10:09:45 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from virt import utils
from ovs import vswitch
from etc import config
import exception


class LibvirtOpenVswitchDriver(object):

    def get_dev_name(_self, instance_id):
        fix = instance_id[0:8]
        bridge_name = 'vbr-%s' % fix
        bridge_port = 'vbase-%s' % fix
        peer_port = 'vpeer%s' % fix
        return bridge_name, bridge_port, peer_port

    def plug(self, instance_id, vmtype):
        try:
            bridge_name, bridge_port, peer_port = self.get_dev_name(instance_id)
            vswitch.ovs_vsctl_add_bridge(bridge_name)
            utils.execute('ip', 'link', 'add', bridge_port, 'type', 'veth', 'peer', 'name', peer_port)
            utils.execute('ip', 'link', 'set', bridge_port, 'up')
            utils.execute('ip', 'link', 'set', peer_port, 'up')
            utils.execute('ip', 'link', 'set', bridge_port, 'promisc', 'on')
            utils.execute('ip', 'link', 'set', peer_port, 'promisc', 'on')
            vswitch.ovs_vsctl_add_port_to_bridge(bridge_name, bridge_port)
            if vmtype == 0:
                bridge = config.control_br
            else:
                bridge = config.data_br
            vswitch.ovs_vsctl_add_port_to_bridge(bridge, peer_port)
            return bridge_name
        except:
            raise exception.VirtualInterfaceException(instance_id=instance_id)

    def unplug(self, instance_id):
        try:
            bridge_name, bridge_port, peer_port = self.get_dev_name(instance_id)
            utils.execute('ip', 'link', 'del', bridge_port, 'type', 'veth', 'peer', 'name', peer_port)
            vswitch.ovs_vsctl_del_bridge(bridge_name)
            vswitch.ovs_vsctl_del_port(peer_port)
            return bridge_name
        except:
            pass
