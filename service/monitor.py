#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:monitor.py
# Date:Sun Jul 07 01:14:35 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import time
import libvirt
import traceback
from virtinst import util
from virt import libvirtConn
from etc import config
from libs import excutils
import psutil
from libs import log as logging
LOG = logging.getLogger("agent.monitor")


class HostMonitor(libvirtConn.LibvirtConnection):

    def __init__(self):
        super(HostMonitor, self).__init__()

    def __del__(self):
        super(HostMonitor, self).__del__()

    def get_info(self):
        try:
            info = {}
            arch = self.conn.getInfo()[0]
            vcpus = self.conn.getInfo()[2]
            xml_inf = self.conn.getSysinfo(0)
            cpu_Hz = util.get_xml_path(xml_inf, "/sysinfo/processor/entry[6]")
            info['cpu'] = "%s %s %s" % (arch, vcpus, cpu_Hz)
            info['mem'] = '%s' % (self.get_mem_usage()[0] >> 20)
            info['hdd'] = '%s' % (self.get_disk_usage("/")[0] >> 30)
            return info
        except libvirt.libvirtError:
            LOG.error(traceback.print_exc())

    def get_cpu_usage(self):
        return psutil.cpu_percent()

    def get_mem_usage(self):
        return psutil.virtual_memory()

    def get_disk_usage(self, partition):
        return psutil.disk_usage(partition)

    def get_net_usage(self, interface):
        return psutil.network_io_counters(1)[interface]

    def get_usage(self):
        cpuusage = '%s' % self.get_cpu_usage()
        memusage = '%s' % self.get_mem_usage()[2]
        diskusage = '%s' % self.get_disk_usage("/")[3]
        netusage = '%s' % ((self.get_net_usage(config.out_br)[0] >> 20) / 10.0)
        return {'cpu': cpuusage, 'mem': memusage, 'disk': diskusage, 'net': netusage}


class DomainMonitor(libvirtConn.LibvirtConnection):

    def __init__(self, vname):
        super(DomainMonitor, self).__init__(vname)

    def __del__(self):
        super(DomainMonitor, self).__del__()

    def get_info(self):
        info = {}
        info['mem'] = '%s' % self.get_mem()
        info['cpu'] = '%s' % self.get_core()
        info['hdd'] = '%s' % (self.get_hdd()[1] >> 30)
        return info

    def get_cpu_usage(self):
        try:
            nbcore = self.conn.getInfo()[2]
            cpu_use_ago = self.dom.info()[4]
            time.sleep(1)
            cpu_use_now = self.dom.info()[4]
            diff_usage = cpu_use_now - cpu_use_ago
            cpu_usage = 100 * diff_usage / (1 * nbcore * 10 ** 9)
            return cpu_usage
        except libvirt.libvirtError:
            LOG.error(traceback.print_exc())
        except Exception:
            LOG.error(traceback.print_exc())

    def get_mem_usage(self):
        memStat = {}
        try:
            allmem = memStat['all'] = self.conn.getInfo()[1] * 1048576
            dom_mem = memStat['usage'] = self.dom.info()[1] * 1024
            memStat['percent'] = (dom_mem * 100) / allmem
            return memStat
        except libvirt.libvirtError:
            LOG.error(traceback.print_exc())
        except Exception:
            LOG.error(traceback.print_exc())

    def get_disk_usage(self):
        diskStat = {}
        total, err = excutils.execute(
            "qemu-img info %s | grep -i 'disk size:'|awk '{print $3}'" % self.get_hdd()[0])
        usage, err = excutils.execute(
            "qemu-img info %s | grep -i 'virtual size:'|awk '{print $3}'" % self.get_hdd()[0])
        diskStat['all'] = total.strip()
        diskStat['usage'] = usage.strip()
        diskStat['percent'] = float(diskStat['usage'][0:-1]) * 100 / float(diskStat['all'][0:-1])
        if diskStat['percent'] >= 100:
            diskStat['percent'] = 100
        return diskStat

    def get_net_usage(self, interface):
        return psutil.network_io_counters(1)[interface]

    def get_status(self):
        cpuusage = '%s' % self.get_cpu_usage()
        memusage = '%s' % self.get_mem_usage()['percent']
        diskusage = '%s' % self.get_disk_usage()['percent']
        target = self.get_nic_target()
        if target:
            netusage = '%s' % ((self.get_net_usage(target)[0] >> 20) / 10.0)
        else:
            netusage = '0'
        return {'vname': self.vname, 'cpu': cpuusage, 'mem': memusage, 'disk': diskusage, 'net': netusage}


from twisted.web import xmlrpc


class MonitorService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        self.request = None

    def render(self, request):
        self.request = request
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_get_host_info(self):
        host = HostMonitor()
        hostInfo = host.get_info()
        return hostInfo

    def xmlrpc_get_domain_info(self, vname):
        domain = DomainMonitor(vname)
        domainInfo = domain.get_info()
        return domainInfo

    def xmlrpc_get_host_status(self):
        host = HostMonitor()
        cpu_free = 100 - host.get_cpu_usage()
        memStatus = host.get_mem_usage()
        mem_free = "%s" % (memStatus['avail'] >> 20)
        mem_total = "%s" % (memStatus['all'] >> 20)
        diskStatus = host.get_disk_usage()
        return {'cpu': cpu_free, 'mem': {'all': mem_total, 'avail': mem_free}, 'disk': diskStatus}

    def xmlrpc_get_host_status_percent(self):
        host = HostMonitor()
        hoststatus = host.get_status()
        return hoststatus

    def xmlrpc_get_domain_status(self, vname):
        domain = DomainMonitor(vname)
        domainStatus = domain.get_status()
        return domainStatus
