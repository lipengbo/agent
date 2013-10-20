#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:connection.py
# Date:Mon May 27 21:18:13 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import libvirt
from eventlet import tpool
from Cheetah.Template import Template
from libs import log as logging
from etc import config
from virt import images
LOG = logging.getLogger("agent.virt")


class LibvirtConnection(object):

    def __init__(self):
        self._conn = self._get_connection()

    def _get_connection(self, uri='qemu:///system'):
        if config.libvirt_blocking:
            self._conn = self._connect(uri)
        else:
            self._conn = tpool.proxy_call((
                libvirt.virDomain, libvirt.virConnect), self._connect, uri)
        return self._conn

    @staticmethod
    def _connect(uri):
        auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_NOECHOPROMPT],
                'root',
                None]
        return libvirt.openAuth(uri, auth, 0)

    def list_instances(self):
        instances = [self._conn.lookupByID(x).name() for x in self._conn.listDomainsID()]
        instances.extends([x for x in self._conn.listDefineedDomains()])
        return instances

    def instance_exists(self, vname):
        try:
            self._conn.lookupByName(vname)
            return True
        except libvirt.libvirtError:
            return False

    def list_instances_detail(self):
        infos = []
        for domain_id in self._conn.listDomainsID():
            domain = self._conn.lookupByID(domain_id)
            (state, _max_mem, _mem, _num_cpu, _cpu_time) = domain.info()
            infos.append((domain.name(), state))
        return infos

    def get_instance_info(self, vname):
        domain = self._conn.lookupByName(vname)
        return domain.info()

    def get_instance(self, vname):
        vname = self.conn.lookupByName(vname)
        return vname

    def get_xml(self, vname):
        dom = self.get_instance(vname)
        xml = dom.XMLDesc(0)
        xml_spl = xml.split('\n')
        return xml_spl

    def autostart(self, vname):
        dom = self.get_instance(vname)
        return dom.autostart()

    def get_state(self, vname):
        dom = self.get_instance(vname)
        return dom.info()[0]

    def do_action(self, vname, action):
        dom = self.get_instance(vname)
        #op_supported = ('create', 'suspend', 'undefine', 'resume', 'destroy')
        getattr(dom, action)()

    @staticmethod
    def prepare_libvirt_xml(vmInfo):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'vnc_port': vnc_port,
                'nics': nic, nic.name  nic.bridge_name  nic.mac_address
            }
        """
        vmInfo['mem'] = int(vmInfo['mem']) << 10
        vmInfo['type'] = config.domain_type
        libvirt_xml = open(config.libvirt_xml_template).read()
        return Template(libvirt_xml, searchList=[vmInfo])

    @staticmethod
    def prepare_interface_xml(interfaces):
        """
        interfaces is a list of interface
        """
        interface_xml = open(config.injected_network_template).read()
        return Template(interface_xml, searchList=[{'interfaces': interfaces}])

    def create_vm(self, vmInfo, netInfo, key=None):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'img': imageUUID,
                'bridge': bridge,
                'mac': mac,
                'hdd': imageSize 2G,
                'dhcp': 1 or 0, 1 代表dhcp  0 代表静态注入
                'glanceURL': glanceURL,
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
        netXml = self.prepare_interface_xml(netInfo)
        images.create_image(vmInfo['glanceURL'], vmInfo['img'], vmInfo['name'], vmInfo['hdd'], vmInfo['dhcp'], net=netXml, key=key)
        domainXml = self.prepare_libvirt_xml(vmInfo)
        self.conn.defineXML(domainXml)

    def delete_vm(self, vname):
        if self.get_state(vname) != 5:
            self.do_action(vname, 'destroy')
        self.do_action(vname, 'undefine')
        images.delete_image(vname)


class LibvirtOpenVswitchDriver(object):

    def get_dev_name(_self, iface_id):
        return iface_id[0:8]

    def plug(self, instance, network):
        pass

    def unplug(self, instance, network, mapping):
        pass
