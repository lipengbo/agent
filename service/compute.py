#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:compute.py
# Date:Tue Sep 03 13:44:37 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import traceback
import threading
from virt.libvirtConn import LibvirtConnection
from virt.disk.api import inject_data
#from virt.disk.vfs import api as vfs
from common.ccf_client import CCFClient
from etc import config
from etc import constants
from virt.images import fetch_with_wget
from common import log as logging
#from db.models import create_instance
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
        #create_instance(vmInfo, key, 0)
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

    @staticmethod
    def add_sshkeys(vname, keys):
        vm_home = config.image_path + vname
        image = vm_home + '/disk'
        inject_data(image, keys)

    @staticmethod
    def delete_sshkeys(vname, keys):
        pass
        #vm_home = config.image_path + vname
        #image = vm_home + '/disk'
        #try:
            #fs = vfs.VFS.instance_for_image(image, 'qcow2', partition=1)
            #fs.setup()
        #except Exception as e:
            #LOG.warn("Ignoring error injecting data into image (%(e)s)" % {'e': e})
            #return False
        #try:
            #return _delete_key_from_fs(keys, fs)
        #finally:
            #fs.teardown()

    @staticmethod
    def start_vms(vname, action, ofport):
        conn = LibvirtConnection()
        try:
            conn.do_action(vname, action, ofport_request=ofport)
            return True
        except:
            return False

    @staticmethod
    def create_snapshot(vname, snapshot_name, snapshot_desc):
        LibvirtConnection.create_snapshot(vname, snapshot_name, snapshot_desc)

    @staticmethod
    def revert_to_snapshot(vname, snapshot_name):
        LibvirtConnection.revert_to_snapshot(vname, snapshot_name)

    @staticmethod
    def delete_snapshot(vname, snapshot_name):
        LibvirtConnection.delete_snapshot(vname, snapshot_name)

    @staticmethod
    def create_image_from_snapshot(vname, snapshot_name, url, image_meta):
        LibvirtConnection.create_image_from_snapshot(vname, snapshot_name, url, image_meta)

    @staticmethod
    def create_image_from_vm(vname, url, image_meta):
        LibvirtConnection.create_image_from_vm(vname, url, image_meta)


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

    def xmlrpc_add_sshkeys(self, vname, key=None):
        add_sshkeys = ComputeManager.add_sshkeys
        t = threading.Thread(target=add_sshkeys, args=(vname, key))
        t.start()
        return True

    def xmlrpc_delete_sshkeys(self, vname, key=None):
        delete_sshkeys = ComputeManager.delete_sshkeys
        t = threading.Thread(target=delete_sshkeys, args=(vname, key))
        t.start()
        return True

    def xmlrpc_create_snapshot(self, vname, snapshot_name):
        snapshot_desc = "%s %s" % (vname, snapshot_name)
        create_snapshot = ComputeManager.create_snapshot
        t = threading.Thread(target=create_snapshot, args=(vname, snapshot_name, snapshot_desc))
        t.start()
        return True

    def xmlrpc_revert_to_snapshot(self, vname, snapshot_name):
        revert_to_snapshot = ComputeManager.revert_to_snapshot
        t = threading.Thread(target=revert_to_snapshot, args=(vname, snapshot_name))
        t.start()
        return True

    def xmlrpc_delete_snapshot(self, vname, snapshot_name):
        delete_snapshot = ComputeManager.delete_snapshot
        t = threading.Thread(target=delete_snapshot, args=(vname, snapshot_name))
        t.start()
        return True

    def xmlrpc_get_current_snapshot(self, vname):
        conn = LibvirtConnection()
        current_snapshot = conn.get_current_snapshot(vname)
        return current_snapshot

    def xmlrpc_get_parent_snapshot(self, vname, snapshot_name):
        conn = LibvirtConnection()
        parent_snapshot = conn.get_parent_snapshot(vname, snapshot_name)
        return parent_snapshot

    def xmlrpc_create_image_from_snapshot(self, vname, snapshot_name, url, image_meta):
        create_image_from_snapshot = ComputeManager.create_image_from_snapshot
        t = threading.Thread(target=create_image_from_snapshot, args=(vname, snapshot_name, url, image_meta))
        t.start()
        return True

    def xmlrpc_create_image_from_vm(self, vname, url, image_meta):
        create_image_from_vm = ComputeManager.create_image_from_vm
        t = threading.Thread(target=create_image_from_vm, args=(vname, url, image_meta))
        t.start()
        return True

    def xmlrpc_reset_dom_mem_vcpu(self, vname, mem_size=None, vcpu=None):
        conn = LibvirtConnection()
        result1 = True
        result2 = True
        if mem_size:
            result1 = conn.set_dom_mem(vname, mem_size)
        if vcpu:
            result2 = conn.set_dom_vcpu(vname, vcpu)
        return result1 & result2

    def xmlrpc_download_image(self, url, image_uuid):
        target = config.image_path + image_uuid
        t = threading.Thread(target=fetch_with_wget, args=(url, target))
        t.start()
        return True
