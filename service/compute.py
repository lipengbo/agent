#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:compute.py
# Date:Tue Sep 03 13:44:37 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import traceback
from twisted.web import xmlrpc
from virt.libvirtConn import LibvirtConnection
from libs import rpcClient
from libs import exception
from libs import excutils
from ovs import vswitch
from etc import constants
from etc import config
from libs import log as logging
import threading
MUTEX = threading.Lock()
LOG = logging.getLogger("agent.virt")


class ComputeManager(LibvirtConnection):
    def __init__(self):
        super(ComputeManager, self).__init__()

    def __del__(self):
        super(ComputeManager, self).__del__()

    def create_vm_workflow(self, vmInfo, netInfo):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'img': imageUUID,
                'mac': mac,
                'hdd': imageSize 2G,
                'dhcp': 1 or 0,
                'glanceURL': glanceURL,
                'type':0/1/2 0 controller 1 slice 2 gateway
            }
        netInfo:
            {
                'ip': address,
                'netmask': netmask,
                'broadcast': broadcast,
                'gateway': gateway,
                'dns': dns,
            }
        """
        MUTEX.acquire()
        try:
            vmInfo['bridge'] = self.prepare_link(vmInfo['name'], vmInfo['type'])
            if not vmInfo['bridge']:
                raise exception.PrepareLinkError()
            self.create_vm(vmInfo, netInfo)
            self.set_domain_state(vmInfo['name'], constants.DOMAIN_STATE['nostate'])
            return True
        except:
            self.set_domain_state(vmInfo['name'], constants.DOMAIN_STATE['failed'])
            return False
        finally:
            MUTEX.release()

    def delete_vm_workflow(self, vname):
        try:
            self.delete_vm(vname)
            self.del_prepare_link(vname)
            return True
        except:
            LOG.error(traceback.print_exc())
        return False

    def set_domain_state(vname, state):
        try:
            client = rpcClient.get_rpc_client(config.vt_manager_ip, config.vt_manager_port)
            client.set_domain_state(vname, state)
        except:
            LOG.error(traceback.print_exc())

    def prepare_link(self, vname, vmtype):
        fix = vname[0:8]
        bridge_name = 'br%s' % fix
        bridge_port = 'b-%s' % fix
        peer_port = 'p-%s' % fix
        vswitch.ovs_vsctl_add_bridge(bridge_name)
        excutils.execute(['ip', 'link', 'add', bridge_port, 'type', 'veth', 'peer', 'name', peer_port])
        excutils.execute(['ip', 'link', 'set', bridge_port, 'up'])
        excutils.execute(['ip', 'link', 'set', peer_port, 'up'])
        excutils.execute(['ip', 'link', 'set', bridge_port, 'promisc', 'on'])
        excutils.execute(['ip', 'link', 'set', peer_port, 'promisc', 'on'])
        vswitch.ovs_vsctl_add_port_to_bridge(bridge_name, bridge_port)
        if vmtype == 0:
            bridge = config.control_br
        elif vmtype == 1:
            bridge = config.data_br
        vswitch.ovs_vsctl_add_port_to_bridge(bridge, peer_port)
        return bridge_name

    def del_prepare_link(self, vname):
        fix = vname[0:8]
        bridge_name = 'br%s' % fix
        bridge_port = 'b-%s' % fix
        peer_port = 'p-%s' % fix
        excutils.execute(['ip', 'link', 'del', bridge_port, 'type', 'veth', 'peer', 'name', peer_port])
        vswitch.ovs_vsctl_del_bridge(bridge_name)
        return bridge_name


class ComputeService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        self.request = None

    def render(self, request):
        self.request = request
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_get_domain_vnc(self, vname):
        conn = LibvirtConnection()
        port = conn.get_vnc(vname)
        if port:
            return '%s' % port
        return False

    def xmlrpc_get_domain_state(self, vname):
        conn = LibvirtConnection()
        state = conn.get_state(vname)
        return state

    def xmlrpc_do_domain_action(self, vname, action):
        conn = LibvirtConnection()
        try:
            conn.do_action(vname, action)
            return True
        except:
            return False

    def xmlrpc_create_vm(self, vmInfo, netInfo):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'img': imageUUID,
                'mac': mac,
                'hdd': imageSize 2G,
                'dhcp': 1 or 0,
                'glanceURL': glanceURL,
                'type':0/1/2 0 controller 1 slice 2 gateway
            }
        netInfo:
            {
                'ip': address,
                'netmask': netmask,
                'broadcast': broadcast,
                'gateway': gateway,
                'dns': dns,
            }
        """
        create_vm_func = ComputeManager().create_vm_workflow
        t1 = threading.Thread(target=create_vm_func, args=(vmInfo, netInfo))
        t1.start()
        return True

    def xmlrpc_delete_vm(self, vname):
        return ComputeManager().delete_vm_workflow(vname)
