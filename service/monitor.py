#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:monitor.py
# Date:Sun Jul 07 01:14:35 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import time
import libvirt
import traceback
import json
from lxml import etree
from virt.libvirtConn import LibvirtConnection
from virt.images import qemu_img_info
import psutil
from common import log as logging
import re
import platform
NET_DEV_PATTERN = re.compile('^v(net|br|base|peer).*')
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
            doc = etree.fromstring(xml_inf)
            path = './processor'
            ret = doc.findall(path)
            cpu_hz = []
            for node in ret:
                cpu_hz.extend([child.text for child in node.getchildren() if child.get('name') == 'version'])
            info['cpu'] = "%s %s %s" % (arch, vcpus, cpu_hz[0])
            info['vcpus'] = "%s" % vcpus
            info['mem'] = '%s' % (self.get_mem_usage()[0] >> 20)
            info['hdd'] = '%s' % (self.get_disk_usage(sep=False)[0] >> 30)
            info['os'] = platform.platform()
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

    def get_disk_usage(self, sep=True):
        """
        return a dict
        {'sda6': usage(total=350163386368, used=83777933312, free=248598147072, percent=23.9),
        'sda2': usage(total=214643503104, used=53969371136, free=160674131968, percent=25.1),
        'sda3': usage(total=429496725504, used=218062954496, free=211433771008, percent=50.8)}
        """
        if not sep:
            return psutil.disk_usage('/')
        disk_usage = {}
        for partition in psutil.disk_partitions():
            disk_usage[partition[0].rpartition('/')[2]] = psutil.disk_usage(partition[1])
        return disk_usage

    def get_disk_io_status(self, sep=True):
        """
        return a dict
        {'sda6': iostat(read_count=269052, write_count=328787, read_bytes=21520634880, write_bytes=46957727744, read_time=2766852, write_time=72206028),
        'sda3': iostat(read_count=14307, write_count=0, read_bytes=262045696, write_bytes=0, read_time=49840, write_time=0),
        'sda2': iostat(read_count=7895, write_count=32, read_bytes=120766464, write_bytes=155648, read_time=39332, write_time=280),
        """
        disk_list = [partition[0].rpartition('/')[2] for partition in psutil.disk_partitions()]
        disk_io_status = psutil.disk_io_counters(sep)
        for disk_name in disk_io_status.keys():
            if disk_name not in disk_list:
                disk_io_status.pop(disk_name)
        return disk_io_status

    def get_net_io_status(self):
        """
        {'br100': iostat(bytes_sent=211562870, bytes_recv=34420315988, packets_sent=2954086, packets_recv=18654351, errin=0, errout=0, dropin=0, dropout=0),
        'lo': iostat(bytes_sent=18146808, bytes_recv=18146808, packets_sent=110998, packets_recv=110998, errin=0, errout=0, dropin=0, dropout=0),
        'br1': iostat(bytes_sent=31441, bytes_recv=115790, packets_sent=196, packets_recv=1238, errin=0, errout=0, dropin=0, dropout=0),
        'eth0': iostat(bytes_sent=245736901, bytes_recv=38661873571, packets_sent=3376581, packets_recv=34852880, errin=0, errout=0, dropin=0, dropout=0)
        }
        """
        net_io_status = psutil.network_io_counters(1)
        for net_dev in net_io_status.keys():
            if NET_DEV_PATTERN.search(net_dev):
                net_io_status.pop(net_dev)
        return net_io_status

    def get_status(self):
        host_status = {}
        host_status['cpu'] = self.get_cpu_usage()
        host_status['mem'] = self.get_mem_usage()
        host_status['disk'] = self.get_disk_usage()
        host_status['net'] = self.get_net_io_status()
        return json.dumps(host_status)


OLD_CPU_TIME = {}


class DomainMonitor(object):

    def __init__(self, vname):
        super(DomainMonitor, self).__init__()
        self.vname = vname
        self.wrap_conn = LibvirtConnection()
        self.conn = self.wrap_conn._conn
        self.dom = self.wrap_conn.get_instance(vname)
        self.nbcore = self.conn.getInfo()[2]

    def get_old_cpu_time(self):
        global OLD_CPU_TIME
        old_cpu_time = OLD_CPU_TIME.get(self.vname, None)
        if not old_cpu_time:
            OLD_CPU_TIME[self.vname] = old_cpu_time = (self.dom.info()[4], time.time())
        return old_cpu_time

    def get_cpu_usage(self):
        """
        return 52.5
        """
        try:
            old_cpu_time = self.get_old_cpu_time()
            new_cpu_time = (self.dom.info()[4], time.time())
            diff_usage = new_cpu_time[0] - old_cpu_time[0]
            duration = new_cpu_time[1] - old_cpu_time[1]
            cpu_usage = 100 * diff_usage / (duration * self.nbcore * 10 ** 9)
            return cpu_usage
        except libvirt.libvirtError:
            LOG.error(traceback.print_exc())
        except Exception:
            LOG.error(traceback.print_exc())

    def get_mem_usage(self):
        """
        {'total': 262144L, 'percent': 100L, 'free': 0L, 'used': 262144L},
        """
        mem_stat = {}
        try:
            domain_info = self.dom.info()
            mem_stat['total'] = max_mem = domain_info[1]
            mem_stat['used'] = curent_mem = domain_info[2]
            mem_stat['free'] = max_mem - curent_mem
            mem_stat['percent'] = (curent_mem * 100) / max_mem
            return mem_stat
        except libvirt.libvirtError:
            LOG.error(traceback.print_exc())

    def get_disk_usage(self):
        """
        {'total': 214748364800.0, 'percent': 2.25, 'free': 209916526592.0, 'used': 4831838208.0}
        """
        disk_stat = {}
        try:
            img_path = self.wrap_conn.get_hdd(self.vname)
            img_info = qemu_img_info(img_path)
            disk_stat['total'] = img_info.virtual_size
            disk_stat['used'] = img_info.disk_size
            disk_stat['free'] = disk_stat['total'] - disk_stat['used']
            disk_stat['percent'] = (disk_stat['used'] * 100) / disk_stat['total']
            return disk_stat
        except:
            LOG.error(traceback.print_exc())

    def get_net_usage(self):
        """
        {'vnet0': iostat(bytes_sent=211562870, bytes_recv=34420315988, packets_sent=2954086, packets_recv=18654351, errin=0, errout=0, dropin=0, dropout=0),
        'vnet1': iostat(bytes_sent=18146808, bytes_recv=18146808, packets_sent=110998, packets_recv=110998, errin=0, errout=0, dropin=0, dropout=0),
        }
        """
        target_nic = self.wrap_conn.get_nic_target(self.vname)
        net_io_status = psutil.network_io_counters(1)
        for net_dev in net_io_status.keys():
            if net_dev not in target_nic:
                net_io_status.pop(net_dev)
        return net_io_status

    def get_status(self):
        dom_status = {}
        dom_status['cpu'] = self.get_cpu_usage()
        dom_status['mem'] = self.get_mem_usage()
        dom_status['disk'] = self.get_disk_usage()
        dom_status['net'] = self.get_net_usage()
        return json.dumps(dom_status)


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

    def xmlrpc_get_host_status(self):
        host = HostMonitor()
        return host.get_status()

    def xmlrpc_get_domain_status(self, vname):
        domain = DomainMonitor(vname)
        return domain.get_status()
