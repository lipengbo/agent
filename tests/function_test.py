#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:images.py
# Date:Thu Oct 24 13:30:50 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from virt.images import fetch
from service.compute import ComputeManager
import threading


def test_fetch():
    url = 'http://192.168.5.107:9292/v1/images/53807c3b-8d25-4d4f-9249-a798ce0b7013'
    target_file = '/var/lib/libvirt/images/53807c3b-8d25-4d4f-9249-a798ce0b7013'
    out, err = fetch(url, target_file)
    #out, err = utils.trycmd('curl', '--fail', url, '-o', target_file, discard_warnings=True)
    #out, err = utils.trycmd('wget', url, '-O', target_file, discard_warnings=True)
    #out, err = utils.trycmd('wget', '-O', target_file, url, discard_warnings=True)
    print out
    print '-------------------------------------------'
    print err


def _create_vm(vname, network, vm_type):
    vmInfo = {}
    vmInfo['name'] = vname
    vmInfo['mem'] = 256
    vmInfo['cpus'] = 1
    vmInfo['img'] = 'a09273ab-382a-4622-b18c-705fda77bdcc'
    vmInfo['hdd'] = 200
    vmInfo['glanceURL'] = ' http://192.168.5.107:9292/v1/images/a09273ab-382a-4622-b18c-705fda77bdcc'
    vmInfo['network'] = network
    vmInfo['type'] = vm_type
    print '$$$$$$$$$$$$$$$$$$$ create vm result = %s $$$$$$$$$$$$$$$$$$$$$' % ComputeManager.create_domain(vmInfo)


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


def delete_vm():
    agent = ComputeManager()
    agent.delete_domain('fe0aa044-da47-4722-ab88-57d05852a3d9')
    agent.delete_domain('fe0aa045-da47-4722-ab88-57d05852a3d9')
    agent.delete_domain('fe0aa046-da47-4722-ab88-57d05852a3d9')
    #img_file = '/var/lib/libvirt/images/a09273ab-382a-4622-b18c-705fda77bdcc'
    #if os.path.exists(img_file):
        #os.remove(img_file)
