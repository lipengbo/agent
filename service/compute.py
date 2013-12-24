#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:compute.py
# Date:Tue Sep 03 13:44:37 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import traceback
from virt.libvirtConn import LibvirtConnection
from common.ccf_client import CCFClient
from etc import config
from etc import constants
from common import log as logging
import threading
LOG = logging.getLogger("agent")


class ComputeManager(object):

    def __init__(self, *args, **kwargs):
        super(ComputeManager, self).__init__(*args, **kwargs)
        self.conn = LibvirtConnection()

    @staticmethod
    def create_domain(vmInfo, key=None):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'img': imageUUID,
                'hdd': imageSize 2,
                'glanceURL': glanceURL,
                'network': [
                    {'address':'192.168.5.100/29', 'gateway':'192.168.5.1',},
                    {'address':'172.16.0.100/16', 'gateway':'172.16.0.1',},
                ]
                'dns': '8.8.8.8'
                'type': 0 for controller; 1 for vm; 2 for gateway
            }
        """
        try:
            LibvirtConnection.create_vm(vmInfo=vmInfo, key=key)
            state = constants.DOMAIN_STATE['nostate']
        except:
            state = constants.DOMAIN_STATE['failed']
            LOG.error(traceback.print_exc())
        finally:
            ComputeManager._set_domain_state(vmInfo['name'], state=state)

    def delete_domain(self, vname):
        try:
            self.conn.delete_vm(vname)
            return True
        except:
            LOG.error(traceback.print_exc())
            return False

    @staticmethod
    def _set_domain_state(vname, state):
        try:
            result = True
            ccf_client = CCFClient()
            result = ccf_client.set_domain_state(vname, state)
            if not result:
                conn = LibvirtConnection()
                conn.delete_vm(vname)
        except:
            LOG.error(traceback.print_exc())


from twisted.web import xmlrpc


class ComputeService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        self.request = None

    def render(self, request):
        self.request = request
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_get_domain_state(self, vname):
        conn = LibvirtConnection()
        return conn.get_state(vname)

    def xmlrpc_do_domain_action(self, vname, action, ofport=None):
        conn = LibvirtConnection()
        try:
            conn.do_action(vname, action, ofport_request=ofport)
            return True
        except:
            return False

    def xmlrpc_get_vnc_port(self, vname):
        conn = LibvirtConnection()
        return conn.get_vnc_port(vname)

    def xmlrpc_create_vm(self, vmInfo, key=None):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'img': imageUUID,
                'hdd': imageSize 2,
                'glanceURL': glanceURL,
                'network': [
                    {'address':'192.168.5.100/29', 'gateway':'192.168.5.1',},
                    {'address':'172.16.0.100/16', 'gateway':'172.16.0.1',},
                ]
                'dns': '8.8.8.8'
                'type': 0 for controller; 1 for vm; 2 for gateway
            }
        """
        create_vm_func = ComputeManager().create_domain
        t = threading.Thread(target=create_vm_func, args=(vmInfo, key))
        t.start()
        return True

    def xmlrpc_delete_vm(self, vname):
        return ComputeManager().delete_domain(vname)

    def xmlrpc_instances_count(self):
        try:
            conn = LibvirtConnection()
            return len(conn.list_instances())
        except:
            import traceback
            LOG.debug(traceback.print_exc())
            return config.domain_count_infinity
