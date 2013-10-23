#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:connection.py
# Date:Mon May 27 21:18:13 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
import libvirt
import shutil
from lxml import etree
from eventlet import tpool
from Cheetah.Template import Template
from etc import config
from virt import images
from virt import utils
from virt.disk import api as disk_api
from virt.vif import LibvirtOpenVswitchDriver
import exception
from common import log as logging
from etc import constants
LOG = logging.getLogger("agent.virt")
VM_TYPE = {'controller': 0, 'slice_vm': 1, 'gateway': 2}


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
        vname = self._conn.lookupByName(vname)
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
        try:
            dom = self.get_instance(vname)
            return dom.info()[0]
        except:
            return constants.DOMAIN_STATE['notexist']

    def get_vnc_port(self, vname):
        target = []
        try:
            dom = self.get_instance(vname)
            xml = dom.XMLDesc(0)
            doc = etree.fromstring(xml)
            path = './devices/graphics'
            ret = doc.findall(path)
            for node in ret:
                target.append(node.get('port'))
        except:
            pass
        return target[0]

    def get_hdd(self, vname):
        target = []
        try:
            dom = self.get_instance(vname)
            xml = dom.XMLDesc(0)
            doc = etree.fromstring(xml)
            path = './devices/disk'
            ret = doc.findall(path)
            for node in ret:
                target.extend([child.get('file') for child in node.getchildren() if child.tag == 'source'])
        except:
            pass
        return target[0]

    def get_nic_target(self, vname):
        target = []
        try:
            dom = self.get_instance(vname)
            xml = dom.XMLDesc(0)
            doc = etree.fromstring(xml)
            path = './devices/interface'
            ret = doc.findall(path)
            for node in ret:
                target.extend([child.get('dev') for child in node.getchildren() if child.tag == 'target'])
        except:
            pass
        return target

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

    def create_vm(self, vmInfo, interfaces, key=None):
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
        #step 0: data prepare
        image_url = vmInfo.pop('glanceURL')
        image_uuid = vmInfo.pop('img')
        disk_size = vmInfo.pop('hdd')
        vm_type = vmInfo.pop('type')
        #step 1: fetch image from glance
        try:
            target_image = config.image_path + image_uuid
            out, err = images.fetch(image_url, target_image)
            if err:
                raise exception.DownloadImageException(image_uuid=image_uuid)
        except:
            if os.path.exists(target_image):
                shutil.rmtree(target_image)
            raise
        #step 2: create image for vm
        try:
            vm_home = config.image_path + vmInfo['name']
            utils.execute('mkdir', '-p', vm_home)
            vm_image = vm_home + '/disk'
            out, err = images.create_cow_image(target_image, vm_image, disk_size)
            if err:
                raise exception.CreateImageException(instance_id=vmInfo['name'])
        except:
            if os.path.exists(vm_home):
                shutil.rmtree(vm_home)
            raise
        #step 3: inject data into vm
        try:
            if (vm_type != VM_TYPE['slice_vm']) and interfaces:
                netXml = self.prepare_interface_xml(interfaces)
                disk_api.inject_data(vm_image, net=netXml, key=key, partition=1)
            if vm_type == VM_TYPE['gateway']:
                LOG.debug('inject dhcp data into gateway')
        except:
            if os.path.exists(vm_home):
                shutil.rmtree(vm_home)
            raise
        #step 4: prepare link for binding to ovs
        ovs_driver = LibvirtOpenVswitchDriver()
        try:
            ovs_driver.plug(vmInfo['name'], vm_type)
        except:
            if os.path.exists(vm_home):
                shutil.rmtree(vm_home)
            ovs_driver.unplug(vmInfo['name'])
            raise
        #step 5: define network
        try:
            domainXml = self.prepare_libvirt_xml(vmInfo)
            self._conn.defineXML(domainXml)
        except:
            if os.path.exists(vm_home):
                shutil.rmtree(vm_home)
            ovs_driver.unplug(vmInfo['name'])
            raise

    def delete_vm(self, vname):
        #step 0: stop vm
        if self.get_state(vname) != 5:
            self.do_action(vname, 'destroy')
        #step 1: undefine vm
        self.do_action(vname, 'undefine')
        #step 2: delete virtual interface
        ovs_driver = LibvirtOpenVswitchDriver()
        ovs_driver.unplug('vname')
        #step 3: clean vm image, delete vm_home
        vm_home = config.image_path + vname
        if os.path.exists(vm_home):
            shutil.rmtree(vm_home)
