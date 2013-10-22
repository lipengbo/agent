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
from virt.libvirtConn import LibvirtConnection
from etc import config
from common import utils
import psutil
from common import log as logging
LOG = logging.getLogger("agent.monitor")


class HostMonitor(object):

    def __init__(self):
        super(HostMonitor, self).__init__()
        self.conn = None

    def get_info(self):
        try:
            info = {}
            if self.conn is None:
                self.conn = LibvirtConnection()._conn
            conn_info = self.conn.getInfo()
            arch = conn_info[0]
            vcpus = conn_info[2]
            xml_inf = self.conn.getSysinfo(0)
            cpu_Hz = util.get_xml_path(xml_inf, "/sysinfo/processor/entry[6]")
            info['cpu'] = "%s %s %s" % (arch, vcpus, cpu_Hz)
            info['vcpus'] = "%s" % vcpus
            info['mem'] = '%s' % (self.get_mem_usage()[0] >> 20)
            info['hdd'] = '%s' % (self.get_disk_usage("/")[0] >> 30)
            return info
        except libvirt.libvirtError:
            LOG.error(traceback.print_exc())

    def get_cpu_usage(self):
        """
        return 52.5
        """
        return psutil.cpu_percent()

    def get_mem_usage(self):
        """
        It's a list
        vmem(total=4037754880L, available=2138624000L, percent=47.0, used=3093798912L, free=943955968L, active=1494089728,
        inactive=1320841216, buffers=507686912L, cached=686981120)
        """
        return psutil.virtual_memory()

    def get_disk_usage(self):
        """
        return a dict
        {'sda6': usage(total=350163386368, used=83777933312, free=248598147072, percent=23.9),
        'sda2': usage(total=214643503104, used=53969371136, free=160674131968, percent=25.1),
        'sda3': usage(total=429496725504, used=218062954496, free=211433771008, percent=50.8)}
        """
        disk_usage = {}
        for partition in psutil.disk_partitions():
            disk_usage[partition[0].rpartition('/')[2]] = psutil.disk_usage(partition[1])
        return disk_usage

    def get_disk_io_status(self):
        """
        return a dict
        {'sda6': iostat(read_count=269052, write_count=328787, read_bytes=21520634880, write_bytes=46957727744, read_time=2766852, write_time=72206028),
        'sda3': iostat(read_count=14307, write_count=0, read_bytes=262045696, write_bytes=0, read_time=49840, write_time=0),
        'sda2': iostat(read_count=7895, write_count=32, read_bytes=120766464, write_bytes=155648, read_time=39332, write_time=280),
        """
        disk_list = [partition[0].rpartition('/')[2] for partition in psutil.disk_partitions()]
        disk_io_status = psutil.disk_io_counters(1)
        for disk_name in disk_io_status.keys():
            if disk_name not in disk_list:
                disk_io_status.pop(disk_name)
        return disk_io_status

    def get_net_io_status(self):
        return psutil.network_io_counters(1)

    def get_status(self):
        cpuusage = '%s' % self.get_cpu_usage()
        memusage = '%s' % self.get_mem_usage()[2]
        diskusage = '%s' % self.get_disk_usage("/")[3]
        netusage = '%s' % ((self.get_net_usage(config.data_br)[0] >> 20) / 10.0)
        return {'cpu': cpuusage, 'mem': memusage, 'disk': diskusage, 'net': netusage}


class DomainMonitor(object):

    def __init__(self, vname):
        super(DomainMonitor, self).__init__()
        self.conn = LibvirtConnection()._conn
        self.dom = self.conn.get_instance(vname)

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
        total, err = utils.execute(
            "qemu-img info %s | grep -i 'disk size:'|awk '{print $3}'" % self.get_hdd()[0])
        usage, err = utils.execute(
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
        cpu_percent = host.get_cpu_usage()
        mem_usage = host.get_mem_usage()
        mem_percent = mem_usage[2]
        mem_free = "%s" % (mem_usage[1] >> 20)
        mem_total = "%s" % (mem_usage[0] >> 20)
        disk_free = "%s" % (host.get_disk_usage('/')[2] >> 30)
        return {'cpu_percent': cpu_percent, 'mem': {'total': mem_total, 'free': mem_free, 'percent': mem_percent}, 'disk_free': disk_free}

    def xmlrpc_get_host_status_percent(self):
        host = HostMonitor()
        hoststatus = host.get_status()
        return hoststatus

    def xmlrpc_get_domain_status(self, vname):
        domain = DomainMonitor(vname)
        domainStatus = domain.get_status()
        return domainStatus

    def xmlrpc_get_domain_state(self, vname):
        host = HostMonitor()
        domain_state = host.get_state(vname)
        return domain_state
