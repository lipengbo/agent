#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:compute.py
# Date:Tue Sep 03 13:44:37 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import traceback
from twisted.web import xmlrpc
from virt.libvirtConn import LibvirtConnection
from common import xml_rpc_client
from etc import constants
from etc import config
from common import log as logging
import threading
MUTEX = threading.Lock()
LOG = logging.getLogger("agent")


class ComputeManager(object):

    def __init__(self):
        self.conn = LibvirtConnection()

    def create_domain(self, vmInfo, interfaces, files=None, key=None):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'img': imageUUID,
                'hdd': imageSize 2,
                'glanceURL': glanceURL,
                'vnc_port': vnc_port,
                'nics': [{'bridge_name': bridge1, 'mac_address': mac1}, {'bridge_name': bridge2, 'mac_address': mac2}],
                'type': 0 for controller; 1 for vm; 2 for gateway
            }
        'interfaces' = [
                        {'name': dev_name, 'address': address, 'netmask': netmask, 'broadcast':broadcast, 'gateway': gateway, 'dns': dns},
                        {'name': dev_name, 'address': address, 'netmask': netmask, 'broadcast':broadcast, 'gateway': gateway, 'dns': dns}
                        ]
        """
        self.conn.create_vm(vmInfo=vmInfo, interfaces=interfaces, files=files, key=key)

    def delete_domain(self, vname):
        self.conn.delete_vm(vname)

    def _set_domain_state(self, vname, state):
        try:
            client = xml_rpc_client.get_rpc_client(config.vt_manager_ip, config.vt_manager_port)
            client.set_domain_state(vname, state)
        except:
            LOG.error(traceback.print_exc())


class ComputeService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        self.request = None

    def render(self, request):
        self.request = request
        return xmlrpc.XMLRPC.render(self, request)

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
                'hdd': imageSize 2,
                'glanceURL': glanceURL,
                'vnc_port': vnc_port,
                'nics': [{'bridge_name': bridge1, 'mac_address': mac1}, {'bridge_name': bridge2, 'mac_address': mac2}],
                'type': 0 for controller; 1 for vm; 2 for gateway
            }
        'interfaces' = [
                        {'name': dev_name, 'address': address, 'netmask': netmask, 'broadcast':broadcast, 'gateway': gateway, 'dns': dns},
                        {'name': dev_name, 'address': address, 'netmask': netmask, 'broadcast':broadcast, 'gateway': gateway, 'dns': dns}
                        ]
        """
        create_vm_func = ComputeManager().create_vm_workflow
        t1 = threading.Thread(target=create_vm_func, args=(vmInfo, netInfo))
        t1.start()
        return True

    def xmlrpc_delete_vm(self, vname):
        return ComputeManager().delete_vm_workflow(vname)
