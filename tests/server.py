#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:service.py
# Date:Fri Oct 25 17:12:12 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import time
import threading
from common.agent_client import AgentClient
from common import log as logging
from common.ovs_client import get_portid_by_name
LOG = logging.getLogger("agent.virt")


def get_domain_status(vname):
    agent = AgentClient('127.0.0.1')
    LOG.debug('----------- start domain status -----%s------------------------' % vname)
    LOG.debug(agent.get_domain_status(vname))
    LOG.debug('----------- end domain status -----%s------------------------' % vname)


def get_host_status():
    agent = AgentClient('127.0.0.1')
    return agent.get_host_status()


def get_host_info():
    agent = AgentClient('127.0.0.1')
    return agent.get_host_info()


def create_vm():
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
    t1 = threading.Thread(target=create_controller)
    t2 = threading.Thread(target=create_slice_vm)
    t3 = threading.Thread(target=create_gateway)
    t1.start()
    t2.start()
    t3.start()


def _create_vm(vname, network, vm_type):
    agent = AgentClient('127.0.0.1')
    vmInfo = {}
    vmInfo['name'] = vname
    vmInfo['mem'] = 256
    vmInfo['cpus'] = 1
    vmInfo['img'] = 'a09273ab-382a-4622-b18c-705fda77bdcc'
    vmInfo['hdd'] = 200
    vmInfo['glanceURL'] = ' http://192.168.5.107:9292/v1/images/a09273ab-382a-4622-b18c-705fda77bdcc'
    vmInfo['network'] = network
    vmInfo['type'] = vm_type
    print '$$$$$$$$$$$$$$$$$$$ create vm result = %s $$$$$$$$$$$$$$$$$$$$$' % agent.create_vm(vmInfo)


def create_controller():
    vname = 'fe0aa044-da47-4722-ab88-57d05852a3d9'
    network = [{'address': '172.16.0.100/16', 'gateway': '172.16.0.1'}]
    vm_type = 0
    _create_vm(vname, network, vm_type)


def create_slice_vm():
    vname = 'fe0aa045-da47-4722-ab88-57d05852a3d9'
    network = [{'address': '192.168.5.100/29', 'gateway': '192.168.1.101'}]
    vm_type = 1
    _create_vm(vname, network, vm_type)


def create_gateway():
    vname = 'fe0aa046-da47-4722-ab88-57d05852a3d9'
    network = [
        {'address': '172.16.0.102/16', 'gateway': '172.16.0.1'},
        {'address': '192.168.5.200/29', 'gateway': '192.168.5.201'},
    ]
    vm_type = 2
    _create_vm(vname, network, vm_type)


def delete_vm():
    agent = AgentClient('127.0.0.1')
    agent.delete_vm('fe0aa044-da47-4722-ab88-57d05852a3d9')
    agent.delete_vm('fe0aa045-da47-4722-ab88-57d05852a3d9')
    agent.delete_vm('fe0aa046-da47-4722-ab88-57d05852a3d9')
    #img_file = '/var/lib/libvirt/images/a09273ab-382a-4622-b18c-705fda77bdcc'
    #if os.path.exists(img_file):
        #os.remove(img_file)


def get_instances_count():
    agent = AgentClient('127.0.0.1')
    return agent.get_instances_count()


def do_domain_action(self, vname, action):
    agent = AgentClient('127.0.0.1')
    return agent.do_domain_action(vname, action)


def get_domain_state(self, vname):
    agent = AgentClient('127.0.0.1')
    return agent.get_domain_state(vname)


def get_vnc_port(self, vname):
    agent = AgentClient('127.0.0.1')
    return agent.get_vnc_port(vname)


def get_all_domains_status():
    while True:
        t1 = threading.Thread(target=get_domain_status, args=('fe0aa044-da47-4722-ab88-57d05852a3d9',))
        t2 = threading.Thread(target=get_domain_status, args=('fe0aa045-da47-4722-ab88-57d05852a3d9',))
        t3 = threading.Thread(target=get_domain_status, args=('fe0aa046-da47-4722-ab88-57d05852a3d9',))
        t1.setDaemon('True')
        t2.setDaemon('True')
        t3.setDaemon('True')
        t1.start()
        t2.start()
        t3.start()
        time.sleep(1)


def test_get_portid_by_name():
    portid = get_portid_by_name('127.0.0.1', '16e89cb2-f648-429b-aaec-858af712d12b')
    print type(portid)


def test():
    agent = AgentClient('127.0.0.1')
    vname = 'vname'
    #print '---------------------------- start create snapshot snap1 ----------------------------------'
    #agent.create_snapshot(vname, 'snap1')
    #print '---------------------------- stop create snapshot snap1 ----------------------------------'
    #print '---------------------------- get current snapshot %s ----------------------------------' % agent.get_current_snapshot(vname)
    #print '---------------------------- get parent snapshot %s ----------------------------------' % agent.get_parent_snapshot(vname, 'snap1')
    #print '---------------------------- start create snapshot snap2 ----------------------------------'
    #agent.create_snapshot(vname, 'snap2')
    #print '---------------------------- stop create snapshot snap2 ----------------------------------'
    #print '---------------------------- get current snapshot %s ----------------------------------' % agent.get_current_snapshot(vname)
    #print '---------------------------- get parent snapshot %s ----------------------------------' % agent.get_parent_snapshot(vname, 'snap2')
    #agent.delete_snapshot(vname, 'snap1')
    #agent.delete_snapshot(vname, 'snap2')
    snapshot_name = 'snap1'
    url = "http://192.168.5.111:9292"
    image_meta = {'name': 'vname', 'is_public': True, 'container_format': 'ovf', 'disk_format': 'qcow2'}
    agent.create_image_from_vm(vname, url, image_meta)
