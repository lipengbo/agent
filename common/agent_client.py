#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:agent_client.py
# Date:Fri Oct 25 14:08:17 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from xmlrpcclient import get_rpc_client
from etc import config


class AgentClient(object):
    def __init__(self, ip):
        self.ip = ip

    def do_domain_action(self, vname, action, ofport=None):
        client = get_rpc_client(self.ip, config.compute_service_port)
        return client.do_domain_action(vname, action, ofport)

    def get_domain_state(self, vname):
        client = get_rpc_client(self.ip, config.compute_service_port)
        return client.get_domain_state(vname)

    def get_vnc_port(self, vname):
        client = get_rpc_client(self.ip, config.compute_service_port)
        return client.get_vnc_port(vname)

    def create_vm(self, vmInfo):
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
                'type': 0 for controller; 1 for vm; 2 for gateway
            }
        """
        client = get_rpc_client(self.ip, config.compute_service_port)
        return client.create_vm(vmInfo)

    def delete_vm(self, vname):
        client = get_rpc_client(self.ip, config.compute_service_port)
        return client.delete_vm(vname)

    def get_instances_count(self):
        client = get_rpc_client(self.ip, config.compute_service_port)
        return client.instances_count()

    def get_host_info(self):
        client = get_rpc_client(self.ip, config.monitor_service_port)
        return client.get_host_info()

    def get_host_status(self):
        client = get_rpc_client(self.ip, config.monitor_service_port)
        return client.get_host_status()

    def get_domain_status(self, vname):
        client = get_rpc_client(self.ip, config.monitor_service_port)
        return client.get_domain_status(vname)
