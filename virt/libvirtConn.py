#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:connection.py
# Date:Mon May 27 21:18:13 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import libvirt
from libvirt import virConnect
import virtinst.util as util
import traceback
from libs import log as logging
from etc import config
from virt import images
from libs.exception import CreateImageError
LOG = logging.getLogger("agent.virt")


class LibvirtConnection(object):

    def __init__(self, ipaddr="127.0.0.1", username=config.libvirt_user, passwd=config.libvirt_passwd):
        self.__ipaddr = ipaddr
        self.__username = username
        self.__passwd = passwd
        self.conn = self.get_conn()

    def __del__(self):
        if isinstance(self.conn, virConnect):
            self.conn.close()

    def __tcp_connection(self, ipaddr, username, passwd):
        def creds(credentials, user_data):
            for credential in credentials:
                if credential[0] == libvirt.VIR_CRED_AUTHNAME:
                    credential[4] = username
                    if len(credential[4]) == 0:
                        credential[4] = credential[3]
                elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
                    credential[4] = passwd
                else:
                    return -1
            return 0
        flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
        auth = [flags, creds, None]
        url = "qemu+tcp://" + ipaddr + "/system"
        conn = libvirt.openAuth(url, auth, 0)
        return conn

    def __connection(self, ipaddr):
        url = "qemu://" + ipaddr + "/system"
        conn = None
        try:
            conn = libvirt.open(url)
        except libvirt.libvirtError:
            LOG.debug(traceback.print_exc())
        return conn

    def get_conn(self):
        conn = None
        try:
            conn = self.__tcp_connection(self.__ipaddr, self.__username, self.__passwd)
        except libvirt.libvirtError:
            conn = self.__connection(self.__ipaddr)
        return conn

    def get_all_vm(self):
        vname = {}
        if self.conn:
            for id in self.conn.listDomainsID():
                id = int(id)
                dom = self.conn.lookupByID(id)
                vname[dom.name()] = dom.info()[0]
            for name in self.conn.listDefinedDomains():
                dom = self.conn.lookupByName(name)
                vname[dom.name()] = dom.info()[0]
        return vname

    def get_emulator(self):
        emulator = []
        if self.conn:
            xml = self.conn.getCapabilities()
            arch = self.conn.getInfo()[0]
            if arch == 'x86_64':
                emulator.append(util.get_xml_path(
                    xml, "/capabilities/guest[1]/arch/emulator"))
                emulator.append(util.get_xml_path(
                    xml, "/capabilities/guest[2]/arch/emulator"))
            else:
                emulator = util.get_xml_path(
                    xml, "/capabilities/guest/arch/emulator")
        return emulator

    def get_machine(self):
        machine = None
        if self.conn:
            xml = self.conn.getCapabilities()
            machine = util.get_xml_path(xml, "/capabilities/guest/arch/machine/@canonical")
        return machine

    def get_dom(self, vname):
        if self.dom:
            return self.dom
        if self.conn:
            try:
                dom = self.conn.lookupByName(self.vname)
            except libvirt.libvirtError:
                dom = None
        return dom

    def get_power_state(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            state = self.dom.isActive()
            return state

    def get_xml(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            xml_spl = xml.split('\n')
            return xml_spl

    def get_mem(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            mem = util.get_xml_path(xml, "/domain/currentMemory")
            mem = int(mem) << 10
            return mem

    def get_core(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            cpu = util.get_xml_path(xml, "/domain/vcpu")
            return cpu

    def get_vnc(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            vnc = util.get_xml_path(xml, "/domain/devices/graphics/@port")
            return vnc

    def get_hdd(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            hdd_path = util.get_xml_path(
                xml, "/domain/devices/disk[1]/source/@file")
            hdd_fmt = util.get_xml_path(
                xml, "/domain/devices/disk[1]/driver/@type")
            size = self.dom.blockInfo(hdd_path, 0)[0]
            # image = re.sub('\/.*\/', '', hdd_path)
            return hdd_path, size, hdd_fmt

    def get_arch(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            arch = util.get_xml_path(xml, "/domain/os/type/@arch")
            return arch

    def get_nic(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            mac = util.get_xml_path(
                xml, "/domain/devices/interface/mac/@address")
            nic = util.get_xml_path(
                xml, "/domain/devices/interface/source/@network")
            if nic is None:
                nic = util.get_xml_path(
                    xml, "/domain/devices/interface/source/@bridge")
            return mac, nic

    def get_nic_target(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            xml = self.dom.XMLDesc(0)
            target = util.get_xml_path(xml, '/domain/devices/interface/target/@dev')
            return target

    def autostart(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            return self.dom.autostart()

    def get_state(self, vname):
        self.dom = self.get_dom(vname)
        if self.dom:
            return self.dom.info()[0]

    def do_action(self, vname, action):
        self.dom = self.get_dom(vname)
        op_supported = ('create', 'suspend', 'undefine', 'resume', 'destroy')
        if action in op_supported:
            getattr(self.dom, action)()
        else:
            from libs.exception import ActionError
            raise ActionError("domain only contains action= %s" % action)

    def to_xml(self, vmInfo):
        """
        vmInfo:
            {
                'name': name,
                'mem': mem,
                'cpus': cpus,
                'img': img,
                'bridge': bridge,
                'mac': mac,
            }
        """
        vmInfo['arch'] = self.conn.getInfo()[0]
        if vmInfo['arch'] == 'x86_64':
            vmInfo['emulator'] = self.get_emulator()[1]
        else:
            vmInfo['emulator'] = self.get_emulator()
        vmInfo['machine'] = self.get_machine()
        vmInfo['mem'] = int(vmInfo['mem']) << 10
        vmInfo['domain_type'] = config.domain_type
        vmInfo['disk_type'] = config.disk_type
        vmInfo['target_port'] = vmInfo['name'][0:8]
        with open(config.libvirt_xml_template) as f:
            xml = f.read()
        return xml % vmInfo

    def to_interface_xml(self, netInfo):
        """
        netInfo:
            {
                'ip': address,
                'netmask': netmask,
                'broadcast': broadcast,
                'gateway': gateway,
                'dns': dns,
            }
        """
        with open(config.injected_network_template) as f:
            xml = f.read()
        return xml % netInfo

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
                'dhcp': 1 or 0,
                'glanceURL': glanceURL,
            }
        """
        netXml = self.to_interface_xml(netInfo)
        if images.create_image(vmInfo['glanceURL'], vmInfo['img'], vmInfo['name'], vmInfo['hdd'], vmInfo['dhcp'], net=netXml, key=key):
            domainXml = self.to_xml(vmInfo)
            self.conn.defineXML(domainXml)
        else:
            raise CreateImageError()

    def delete_vm(self, vname):
        if self.get_state(vname) != 5:
            self.do_action('destroy')
        self.do_action('undefine')
        images.delete_image(config.image_path, vname)
