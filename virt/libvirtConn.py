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
from virt import utils
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
                'nics': [{'bridge_name': bridge1, 'mac_address': mac1}, {'bridge_name': bridge2, 'mac_address': mac2}]
            }
        """
        vmInfo['mem'] = int(vmInfo['mem']) << 10
        vmInfo['basepath'] = config.image_path + vmInfo['name']
        libvirt_xml = open(config.libvirt_xml_template).read()
        return str(Template(libvirt_xml, searchList=[vmInfo]))

    @staticmethod
    def prepare_interface_xml(interfaces):
        """
        interfaces is a list of interface
            'interfaces' = [
                           {'name': dev_name, 'address': address, 'netmask': netmask, 'broadcast':broadcast, 'gateway': gateway, 'dns': dns},
                           {'name': dev_name, 'address': address, 'netmask': netmask, 'broadcast':broadcast, 'gateway': gateway, 'dns': dns}
                           ]
        """
        interface_xml = open(config.injected_network_template).read()
        return str(Template(interface_xml, searchList=[{'interfaces': interfaces}]))

    def create_vm(self, vmInfo, interfaces, files=None, key=None):
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
        #step 1: fetch image from glance
        image_url = vmInfo.pop('glanceURL')
        image_uuid = vmInfo.pop('img')
        target_image = config.image_path + image_uuid
        out, err = images.fetch(image_url, target_image)
        if err:
            raise Exception('Download image=%s failed' % image_uuid)
        #step 2: create image for vm
        vm_home = config.image_path + vmInfo['name']
        utils.execute('mkdir', '-p', vm_home)
        vm_image = vm_home + '/disk'
        disk_size = vmInfo['hdd']
        out, err = images.create_cow_image(target_image, vm_image, disk_size)
        if err:
            utils.execute('rm', '-rf', vm_home)
            raise Exception('Download image=%s failed' % image_uuid)
        #step 3: inject data into vm
        netXml = self.prepare_interface_xml(interfaces)
        #step 4: prepare link for binding to ovs
        #step 5: define network
        domainXml = self.prepare_libvirt_xml(vmInfo)
        self.conn.defineXML(domainXml)

    def delete_vm(self, vname):
        if self.get_state(vname) != 5:
            self.do_action(vname, 'destroy')
        self.do_action(vname, 'undefine')
        images.delete_image(vname)
