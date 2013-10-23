#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:compte.py
# Date:Wed Oct 23 23:15:12 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from service.compute import ComputeService
import threading


compute_service = ComputeService()


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


def create_controller():
    vmInfo = {}
    vmInfo['name'] = 'fe0aa044-da47-4722-ab88-57d05852a3d9'
    vmInfo['mem'] = 64
    vmInfo['cpus'] = 1
    vmInfo['img'] = '3b9db5fd-77d5-4387-8831-3241e91f1f56'
    vmInfo['hdd'] = 1
    vmInfo['glanceURL'] = 'http://192.168.5.107/v2/images/3b9db5fd-77d5-4387-8831-3241e91f1f56'
    vmInfo['network'] = [{'address': '172.16.0.100/16', 'gateway': '172.16.0.1'}]
    vmInfo['type'] = 0
    compute_service.xmlrpc_create_vm(vmInfo)


def create_slice_vm():
    vmInfo = {}
    vmInfo['name'] = 'fe0aa045-da47-4722-ab88-57d05852a3d9'
    vmInfo['mem'] = 64
    vmInfo['cpus'] = 1
    vmInfo['img'] = '3b9db5fd-77d5-4387-8831-3241e91f1f56'
    vmInfo['hdd'] = 1
    vmInfo['glanceURL'] = 'http://192.168.5.107/v2/images/3b9db5fd-77d5-4387-8831-3241e91f1f56'
    vmInfo['network'] = [{'address': '192.168.5.100/29', 'gateway': '192.168.1.101'}]
    vmInfo['type'] = 1
    compute_service.xmlrpc_create_vm(vmInfo)


def create_gateway():
    vmInfo = {}
    vmInfo['name'] = 'fe0aa046-da47-4722-ab88-57d05852a3d9'
    vmInfo['mem'] = 64
    vmInfo['cpus'] = 1
    vmInfo['img'] = '3b9db5fd-77d5-4387-8831-3241e91f1f56'
    vmInfo['hdd'] = 1
    vmInfo['glanceURL'] = 'http://192.168.5.107/v2/images/3b9db5fd-77d5-4387-8831-3241e91f1f56'
    vmInfo['network'] = [
        {'address': '172.16.0.102/16', 'gateway': '172.16.0.1'},
        {'address': '192.168.5.200/29', 'gateway': '192.168.5.201'},
    ]
    vmInfo['type'] = 2
    compute_service.xmlrpc_create_vm(vmInfo)


def delete_vm():
    compute_service.xmlrpc_delete_vm('fe0aa044-da47-4722-ab88-57d05852a3d9')
    compute_service.xmlrpc_delete_vm('fe0aa045-da47-4722-ab88-57d05852a3d9')
    compute_service.xmlrpc_delete_vm('fe0aa046-da47-4722-ab88-57d05852a3d9')
