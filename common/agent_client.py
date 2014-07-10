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

    def do_domain_action(self, vname, action, ofport=None, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.do_domain_action(vname, action, ofport)

    def get_domain_state(self, vname, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.get_domain_state(vname)

    def get_vnc_port(self, vname, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.get_vnc_port(vname)

    def add_route_to_vpnserver(self, net, gw, timeout=None):
        client = get_rpc_client(self.ip, config.vpn_service_port, timeout)
        return client.add_route(net, gw)

    def del_route_from_vpnserver(self, net, gw, timeout=None):
        client = get_rpc_client(self.ip, config.vpn_service_port, timeout)
        return client.del_route(net, gw)

    def create_vm(self, vmInfo, key=None, timeout=None):
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
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.create_vm(vmInfo, key)

    def delete_vm(self, vname, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.delete_vm(vname)

    def get_instances_count(self, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.instances_count()

    def get_host_info(self, timeout=None):
        client = get_rpc_client(self.ip, config.monitor_service_port, timeout)
        return client.get_host_info()

    def get_host_status(self, timeout=None):
        client = get_rpc_client(self.ip, config.monitor_service_port, timeout)
        return client.get_host_status()

    def get_domain_status(self, vname, timeout=None):
        client = get_rpc_client(self.ip, config.monitor_service_port, timeout)
        return client.get_domain_status(vname)

    def add_sshkeys(self, vname, key=None, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.add_sshkeys(vname, key)

    def delete_sshkeys(self, vname, key=None, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.delete_sshkeys(vname, key)

    def create_snapshot(self, vname, snapshot_name, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.create_snapshot(vname, snapshot_name)

    def revert_to_snapshot(self, vname, snapshot_name, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.revert_to_snapshot(vname, snapshot_name)

    def delete_snapshot(self, vname, snapshot_name, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.delete_snapshot(vname, snapshot_name)

    def get_current_snapshot(self, vname, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.get_current_snapshot(vname)

    def get_parent_snapshot(self, vname, snapshot_name, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.get_parent_snapshot(vname, snapshot_name)

    def create_image_from_snapshot(self, vname, snapshot_name, url, image_meta, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.create_image_from_snapshot(vname, snapshot_name, url, image_meta)

    def create_image_from_vm(self, vname, url, image_meta, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.create_image_from_vm(vname, url, image_meta)

    def reset_dom_mem_vcpu(self, vname, mem_size=None, vcpu=None, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.reset_dom_mem_vcpu(vname, mem_size, vcpu)

    def download_image(self, url, image_uuid, timeout=None):
        client = get_rpc_client(self.ip, config.compute_service_port, timeout)
        return client.download_image(url, image_uuid)
