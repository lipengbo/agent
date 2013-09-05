#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:service.py
# Date:Fri Jul 05 16:24:16 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
import traceback
from libs import excutils as excutils
from etc import config
import threading
from libs import log as logging
MUTEX = threading.Lock()
LOG = logging.getLogger("agent.network")
DHCP_CONF_FILE = '/var/lib/libvirt/dnsmasq/ceni_dhcp.conf'
DHCP_LEASE_MAX = 200000
PID_FILE = '/var/run/ceni_dhcp.pid'
DHCP_LEASEFILE = '/var/lib/libvirt/dnsmasq/ceni_dhcp.leases'
DHCP_HOSTSFILE = '/var/lib/libvirt/dnsmasq/ceni_dhcp.hostsfile'
ADDN_HOSTS = '/var/lib/libvirt/dnsmasq/ceni_dhcp.addnhosts'
DHCP_INTERFACE = config.gateway_service_bridge


class DHCPManager(object):

    def __init__(self, conf_file, lease_max, pid_file, lease_file, host_file, addn_host, interface):
        self.conf_file = conf_file
        self.lease_max = lease_max
        self.pid_file = pid_file
        self.lease_file = lease_file
        self.host_file = host_file
        self.addn_host = addn_host
        self.interface = interface

    def write_to_file(self, file, data, mode='w'):
        with open(file, mode) as f:
            f.write(data)

    def readline_from_file(self, file, mode='r'):
        with open(file, mode) as f:
            for line in f:
                yield line

    def ensure_file(self, file, data):
        if not os.path.isfile(file):
            self.write_to_file(file, data)

    def start(self):
        cmd = "dnsmasq --conf-file=%s" % DHCP_CONF_FILE
        excutils.execute(cmd)

    def get_pid(self):
        cmd = "ps ax| grep -i 'dnsmasq --conf-file=%s'|grep -v grep|awk '{print $1}'" % DHCP_CONF_FILE
        out, err = excutils.execute(cmd)
        if (not err) and out:
            return out
        return False

    def stop(self):
        pid = self.get_pid()
        if pid:
            cmd = "kill -9 %s" % pid
            excutils.execute(cmd)

    def restart(self):
        self.stop()
        self.start()

    def generate_conf(self):
        config = """local=//
    pid-file=%s
    except-interface=lo
    bind-dynamic
    interface=%s
    dhcp-no-override
    dhcp-leasefile=%s
    dhcp-lease-max=%s
    dhcp-hostsfile=%s
    dhcp-option=6, 8.8.8.8
    addn-hosts=%s
    """ % (PID_FILE, DHCP_INTERFACE, DHCP_LEASEFILE, DHCP_LEASE_MAX, DHCP_HOSTSFILE, ADDN_HOSTS)
        self.ensure_file(DHCP_CONF_FILE, config)
        dhcp_file_bak = DHCP_CONF_FILE + ".bak"
        excutils.execute('cp %s %s' % (DHCP_CONF_FILE, dhcp_file_bak))
        return self.readline_from_file(dhcp_file_bak)

    def add_dhcprange(self, netaddr):
        try:
            MUTEX.acquire()
            file_iter = self.generate_conf()
            self.write_to_file(DHCP_CONF_FILE, "", mode='w')
            dhcp_range = "dhcp-range=%s,static\n" % netaddr
            for data in file_iter:
                if data != dhcp_range:
                    self.write_to_file(DHCP_CONF_FILE, data, mode='a')
            self.write_to_file(DHCP_CONF_FILE, dhcp_range, mode='a')
            self.write_to_file(DHCP_LEASEFILE, "", mode='w')
            self.restart()
            result = True
        except:
            LOG.error(traceback.print_exc())
            result = False
        finally:
            MUTEX.release()
            return result

    def del_dhcprange(self, netaddr):
        try:
            MUTEX.acquire()
            file_iter = self.generate_conf()
            self.write_to_file(DHCP_CONF_FILE, "", mode='w')
            dhcp_range = "dhcp-range=%s,static\n" % netaddr
            for data in file_iter:
                if data != dhcp_range:
                    self.write_to_file(DHCP_CONF_FILE, data, mode='a')
            self.write_to_file(DHCP_LEASEFILE, "", mode='w')
            self.restart()
            result = True
        except:
            LOG.error(traceback.print_exc())
            result = False
        finally:
            MUTEX.release()
            return result

    def generate_hostfile(self):
        self.ensure_file(DHCP_HOSTSFILE, "")
        dhcp_file_bak = DHCP_HOSTSFILE + ".bak"
        excutils.execute('cp %s %s' % (DHCP_HOSTSFILE, dhcp_file_bak))
        return self.readline_from_file(dhcp_file_bak)

    def add_host(self, mac, ipaddr):
        try:
            MUTEX.acquire()
            file_iter = self.generate_hostfile()
            self.write_to_file(DHCP_HOSTSFILE, "", mode='w')
            mac_ip = "%s,%s,%s\n" % (mac, ipaddr, ipaddr.replace(".", "_"))
            for data in file_iter:
                if mac not in data:
                    self.write_to_file(DHCP_HOSTSFILE, data, mode='a')
            self.write_to_file(DHCP_HOSTSFILE, mac_ip, mode='a')
            self.write_to_file(DHCP_LEASEFILE, "", mode='w')
            self.restart()
            result = True
        except:
            LOG.error(traceback.print_exc())
            result = False
        finally:
            MUTEX.release()
            return result

    def del_host(self, mac, ipaddr):
        try:
            MUTEX.acquire()
            file_iter = self.generate_hostfile()
            self.write_to_file(DHCP_HOSTSFILE, "", mode='w')
            for data in file_iter:
                if mac not in data:
                    self.write_to_file(DHCP_HOSTSFILE, data, mode='a')
            self.write_to_file(DHCP_LEASEFILE, "", mode='w')
            self.restart()
            result = True
        except:
            LOG.error(traceback.print_exc())
            result = False
        finally:
            MUTEX.release()
            return result


from twisted.web import xmlrpc


class DHCPService(xmlrpc.XMLRPC):

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        self.request = None

    def render(self, request):
        self.request = request
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_add_dhcprange(self, netaddr):
        """
        When a network created this function must be called
        """
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.add_dhcprange(netaddr)

    def xmlrpc_del_dhcprange(self, netaddr):
        """
        When a network deleted this function must be called
        """
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.del_dhcprange(netaddr)

    def xmlrpc_start(self, netaddr):
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.start()

    def xmlrpc_stop(self, netaddr):
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.stop()

    def xmlrpc_restart(self, netaddr):
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.restart()

    def xmlrpc_get_pid(self, netaddr):
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.get_pid()

    def xmlrpc_add_host(self, mac, ipaddr):
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.add_host(mac, ipaddr)

    def xmlrpc_del_host(self, mac, ipaddr):
        dhcpHandler = DHCPManager(DHCP_CONF_FILE, DHCP_LEASE_MAX, PID_FILE, DHCP_LEASEFILE, DHCP_HOSTSFILE, ADDN_HOSTS, DHCP_INTERFACE)
        return dhcpHandler.del_host(mac, ipaddr)
