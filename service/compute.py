#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:compute.py
# Date:Tue Sep 03 13:44:37 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import traceback
from virt.libvirtConn import LibvirtConnection
from common import xml_rpc_client
from etc import config
from etc import constants
import threading
from common import log as logging
LOG = logging.getLogger("agent")
MUTEX = threading.RLock()


class ComputeManager(object):

    def __init__(self, *args, **kwargs):
        super(ComputeManager, self).__init__(*args, **kwargs)
        self.conn = LibvirtConnection()

    def create_domain(self, vmInfo, key=None):
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
            MUTEX.acquire()
            self.conn.create_vm(vmInfo=vmInfo, key=key)
        except:
            LOG.error(traceback.print_exc())
            self._set_domain_state(vmInfo['name'], state=constants.DOMAIN_STATE['failed'])
        else:
            state = self.conn.get_state(vmInfo['name'])
            self._set_domain_state(vmInfo['name'], state=state)
        finally:
            MUTEX.release()

    def delete_domain(self, vname):
        try:
            self.conn.delete_vm(vname)
            return True
        except:
            LOG.error(traceback.print_exc())
            return False

    def _set_domain_state(self, vname, state):
        try:
            client = xml_rpc_client.get_rpc_client(config.vt_manager_ip, config.vt_manager_port)
            client.set_domain_state(vname, state)
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

    def xmlrpc_do_domain_action(self, vname, action):
        conn = LibvirtConnection()
        try:
            conn.do_action(vname, action)
            return True
        except:
            return False

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
        t1 = threading.Thread(target=create_vm_func, args=(vmInfo, key))
        t1.run()
        return True

    def xmlrpc_delete_vm(self, vname):
        return ComputeManager().delete_domain(vname)
