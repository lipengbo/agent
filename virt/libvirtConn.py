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
from virt.ipam import netaddr
#import exception
from common import log as logging
from etc import constants
from db.models import Domain
LOG = logging.getLogger("agent.virt")
VM_TYPE = {'controller': 0, 'slice_vm': 1, 'gateway': 2}


def patch_tpool_proxy():
    """eventlet.tpool.Proxy doesn't work with old-style class in __str__()
    """
    def str_method(self):
        return str(self._obj)

    def repr_method(self):
        return repr(self._obj)

    tpool.Proxy.__str__ = str_method
    tpool.Proxy.__repr__ = repr_method


patch_tpool_proxy()


class LibvirtConnection(object):

    def __init__(self, *args, **kwargs):
        super(LibvirtConnection, self).__init__(*args, **kwargs)
        self._conn = self._get_connection()

    def _get_connection(self, uri='qemu:///system'):
        if config.libvirt_blocking:
            self._conn = self._connect(uri)
        else:
            self._conn = tpool.proxy_call((
                libvirt.virDomain, libvirt.virConnect), self._connect, uri)
            return self._conn

    @staticmethod
    def _connect(uri='qemu:///system'):
        auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_NOECHOPROMPT],
                'root',
                None]
        return libvirt.openAuth(uri, auth, 0)

    def list_instances(self):
        instances = [self._conn.lookupByID(x).name() for x in self._conn.listDomainsID()]
        instances.extend([x for x in self._conn.listDefinedDomains()])
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
            target.extend([node.get('port') for node in ret if node.get('port') != -1])
            #for node in ret:
                #target.append(node.get('port'))
        except:
            pass
        return target and target[0]

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

    def do_action(self, vname, action, ofport_request=None):
        dom = self.get_instance(vname)
        #op_supported = ('create', 'suspend', 'undefine', 'resume', 'destroy')
        state = None
        if action == 'create':
            if ofport_request:
                portname = 'vdata-%s' % vname[0:8]
                LibvirtOpenVswitchDriver.set_vm_ofport(portname, ofport_request)
            state = 2
        if action == 'destroy':
            LibvirtOpenVswitchDriver.del_vm_port(vname)
            state = 5
        getattr(dom, action)()
        Domain.update(vname, ofport_request, state)

    @staticmethod
    def prepare_libvirt_xml(vmInfo):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'nics': [{'bridge_name': bridge1, 'mac_address': mac1}, {'bridge_name': bridge2, 'mac_address': mac2}]
            }
        """
        vmInfo['mem'] = int(vmInfo['mem']) << 10
        vmInfo['basepath'] = config.image_path + vmInfo['name']
        with open(config.libvirt_xml_template) as f:
            libvirt_xml = f.read()
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
        with open(config.injected_network_template) as f:
            interface_xml = f.read()
        return str(Template(interface_xml, searchList=[{'interfaces': interfaces}]))

    @staticmethod
    def prepare_dhcp_conf(**dhcp_conf):
        """
        dhcp_conf:
            {
                'ip_start': '192.168.5.2',
                'netsize': 5,
                'gateway': '192.168.5.1',
            }
        """
        with open(config.dhcp_conf) as f:
            dhcp_conf_content = f.read()
        return str(Template(dhcp_conf_content, searchList=[dhcp_conf]))

    @staticmethod
    def prepare_dhcp_hostfile(mac_ip_list):
        """
        mac_ip_list = (('00:e0:4c:52:ff:53', '192.168.1.1'),('00:e0:4c:52:ff:54', '192.168.1.2'))
        """
        with open(config.dhcp_hostfile) as f:
            dhcp_hostfile_content = f.read()
        return str(Template(dhcp_hostfile_content, searchList=[{'mac_ip_list': mac_ip_list}]))

    @staticmethod
    def prepare_dhcp_files(netInfo):
        """
            {'address':'192.168.5.100/29', 'gateway':'192.168.5.1',}
        """
        network_addr = netInfo.get('address')
        gateway = netInfo.get('gateway')
        network = netaddr.Network(network_addr)
        ip_start = str(network.get_host(1))
        netsize = network.size
        dhcp_conf_content = LibvirtConnection.prepare_dhcp_conf(ip_start=ip_start, netsize=netsize, gateway=gateway)
        mac_ip_list = []
        for host_ip in network.iter_hosts():
            mac_ip_list.append((netaddr.generate_mac_address(host_ip), host_ip))
        dhcp_hostfile_content = LibvirtConnection.prepare_dhcp_hostfile(mac_ip_list=mac_ip_list)
        return ((config.dhcp_conf_target, dhcp_conf_content), (config.dhcp_hostfile_target, dhcp_hostfile_content))

    @staticmethod
    def create_vm(vmInfo, key=None):
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
        #step 0: data prepare
        image_url = vmInfo.pop('glanceURL')
        image_uuid = vmInfo.pop('img')
        disk_size = vmInfo.pop('hdd')
        vm_type = vmInfo.pop('type')
        #step 1: fetch image from glance
        try:
            target_image = config.image_path + image_uuid
            images.fetch(image_url, target_image)
            #if err:
                #raise exception.DownloadImageException(image_uuid=image_uuid)
        except:
            if os.path.exists(target_image):
                os.remove(target_image)
            raise
        #step 2: create image for vm
        try:
            vm_home = config.image_path + vmInfo['name']
            utils.execute('mkdir', '-p', vm_home)
            vm_image = vm_home + '/disk'
            images.create_cow_image(target_image, vm_image, disk_size)
            #if err:
                #raise exception.CreateImageException(instance_id=vmInfo['name'])
        except:
            if os.path.exists(vm_home):
                shutil.rmtree(vm_home)
            raise
        #step 3: inject data into vm
        #ovs_driver = LibvirtOpenVswitchDriver()
        try:
            nics = []
            interfaces = []
            net_dev_index = 0
            network = vmInfo.pop('network', None)
            for net in network:
                address = net.get('address', '0.0.0.0/0')
                nic = {}
                nic['mac_address'] = netaddr.generate_mac_address(netaddr.clean_ip(address))
                if net_dev_index == 1:
                    nic['bridge_name'] = config.gw_br
                    nic['dev'] = 'vgate-%s' % vmInfo['name'][0:8]
                elif vm_type != 0:
                    nic['bridge_name'] = config.data_br
                    nic['dev'] = 'vdata-%s' % vmInfo['name'][0:8]
                else:
                    nic['bridge_name'] = config.control_br
                    nic['dev'] = 'vcontr-%s' % vmInfo['name'][0:8]
                    #nic['bridge_name'] = ovs_driver.get_dev_name(vmInfo['name'])[0]
                nics.append(nic)
                netaddr_network = netaddr.Network(address)
                ifc = {}
                ifc['name'] = 'eth%s' % net_dev_index
                ifc['address'] = netaddr.clean_ip(address)
                ifc['netmask'] = str(netaddr_network.netmask)
                ifc['broadcast'] = str(netaddr_network.broadcast)
                ifc['gateway'] = net.get('gateway', netaddr_network.get_first_host())
                ifc['dns'] = vmInfo.pop('dns', '8.8.8.8')
                ifc['vm_type'] = vm_type
                interfaces.append(ifc)
                interfaces.reverse()
                net_dev_index = net_dev_index + 1
            vmInfo['nics'] = nics
            files = None
            netXml = None
            if vm_type == VM_TYPE['gateway']:
                LOG.debug('inject dhcp data into gateway')
                files = LibvirtConnection.prepare_dhcp_files(network[0])
            if vm_type != VM_TYPE['slice_vm']:
                netXml = LibvirtConnection.prepare_interface_xml(interfaces)
            disk_api.inject_data(vm_image, net=netXml, key=key, files=files, partition=1)
        except:
            if os.path.exists(vm_home):
                shutil.rmtree(vm_home)
            raise
        #step 4: prepare link for binding to ovs
        #try:
            #ovs_driver.plug(vmInfo['name'], vm_type)
        #except:
            #if os.path.exists(vm_home):
                #shutil.rmtree(vm_home)
            #ovs_driver.unplug(vmInfo['name'])
            #raise
        #step 5: define vm
        try:
            domainXml = LibvirtConnection.prepare_libvirt_xml(vmInfo)
            conn = LibvirtConnection._connect()
            conn.defineXML(domainXml)
        except:
            if os.path.exists(vm_home):
                shutil.rmtree(vm_home)
            #ovs_driver.unplug(vmInfo['name'])
            raise
        #step 6: insert vm recorder into db
        try:
            domain = Domain()
            domain.name = vmInfo['name']
            domain.state = 0
            domain.save()
        except:
            pass
        finally:
            try:
                conn.close()
            except:
                pass

    def delete_vm(self, vname):
        #step 0: stop vm
        if self.get_state(vname) != 5:
            self.do_action(vname, 'destroy')
        #step 1: undefine vm
        self.do_action(vname, 'undefine')
        #step 2: delete virtual interface
        LibvirtOpenVswitchDriver.del_vm_port(vname)
        #step 3: clean vm image, delete vm_home
        vm_home = config.image_path + vname
        if os.path.exists(vm_home):
            shutil.rmtree(vm_home)
        #step 4: delete vm in db
        try:
            Domain.delete(vname)
        except:
            pass
