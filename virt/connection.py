#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:connection.py
# Date:Sat Oct 19 13:50:09 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import libvirt
import utils as libvirt_utils
import multiprocessing
from etc.config import libvirt_blocking
from eventlet import tpool
from eventlet import greenthread


def patch_tpool_proxy():
    """eventlet.tpool.Proxy doesn't work with old-style class in __str__()
    or __repr__() calls.
    This function perform a monkey patch to replace those two instance methods.
    """
    def str_method(self):
        return str(self._obj)

    def repr_method(self):
        return repr(self._obj)

    tpool.Proxy.__str__ = str_method
    tpool.Proxy.__repr__ = repr_method


patch_tpool_proxy()


class LibvirtConnection(object):

    def __init__(self):
        self._conn = self._get_connection()

    def _get_connection(self, uri='qemu:///system'):
        if libvirt_blocking:
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

    def get_num_instances(self):
        return self._conn.numOfDomains()

    def instance_exists(self, instance_id):
        try:
            self._conn.lookupByName(instance_id)
            return True
        except libvirt.libvirtError:
            return False

    def list_instances(self):
        return [self._conn.lookupByID(x).name()
                for x in self._conn.listDomainsID()]

    def list_instances_detail(self):
        infos = []
        for domain_id in self._conn.listDomainsID():
            domain = self._conn.lookupByID(domain_id)
            (state, _max_mem, _mem, _num_cpu, _cpu_time) = domain.info()
            infos.append((domain.name(), state))
        return infos

    def _inject_files(self, instance, files, partition):
        disk_path = os.path.join(FLAGS.instances_path,
                                 instance['name'], 'disk')
        disk.inject_files(disk_path, files, partition=partition,
                          use_cow=FLAGS.use_cow_images)

    @staticmethod
    def get_vcpu_total():
        """Get vcpu number of physical computer.

        :returns: the number of cpu core.

        """
        return multiprocessing.cpu_count()

    def get_memory_mb_total(self):
        """Get the total memory size(MB) of physical computer.

        :returns: the total amount of memory(MB).

        """

        return self._conn.getInfo()[1]

    @staticmethod
    def get_local_gb_total():
        """Get the total hdd size(GB) of physical computer.

        :returns:
            The total amount of HDD(GB).

        """

        stats = libvirt_utils.get_fs_info(FLAGS.instances_path)
        return stats['total'] >> 30

    def get_vcpu_used(self):
        """ Get vcpu usage number of physical computer.

        :returns: The total number of vcpu that currently used.

        """

        total = 0
        for dom_id in self._conn.listDomainsID():
            dom = self._conn.lookupByID(dom_id)
            vcpus = dom.vcpus()
            if vcpus is None:
                # a used count is hardly useful for something measuring usage
                total += 1
            else:
                total += len(vcpus[1])
            greenthread.sleep(0)
        return total

    def get_memory_mb_used(self):
        """Get the free memory size(MB) of physical computer.

        :returns: the total usage of memory(MB).

        """
        m = open('/proc/meminfo').read().split()
        idx1 = m.index('MemFree:')
        idx2 = m.index('Buffers:')
        idx3 = m.index('Cached:')
        avail = (int(m[idx1 + 1]) + int(m[idx2 + 1]) + int(m[idx3 + 1]))
        # Convert it to MB
        return (self.get_memory_mb_total() - avail) >> 10

    def get_hypervisor_type(self):
        """Get hypervisor type.

        :returns: hypervisor type (ex. qemu)

        """

        return self._conn.getType()

    def get_cpu_info(self):
        """Get cpuinfo information.

        Obtains cpu feature from virConnect.getCapabilities,
        and returns as a json string.

        :return: see above description

        """

        xml = self._conn.getCapabilities()
        xml = ElementTree.fromstring(xml)
        nodes = xml.findall('.//host/cpu')
        if len(nodes) != 1:
            reason = _("'<cpu>' must be 1, but %d\n") % len(nodes)
            reason += xml.serialize()
            raise exception.InvalidCPUInfo(reason=reason)

        cpu_info = dict()

        arch_nodes = xml.findall('.//host/cpu/arch')
        if arch_nodes:
            cpu_info['arch'] = arch_nodes[0].text

        model_nodes = xml.findall('.//host/cpu/model')
        if model_nodes:
            cpu_info['model'] = model_nodes[0].text

        vendor_nodes = xml.findall('.//host/cpu/vendor')
        if vendor_nodes:
            cpu_info['vendor'] = vendor_nodes[0].text

        topology_nodes = xml.findall('.//host/cpu/topology')
        topology = dict()
        if topology_nodes:
            topology_node = topology_nodes[0]

            keys = ['cores', 'sockets', 'threads']
            tkeys = topology_node.keys()
            if set(tkeys) != set(keys):
                ks = ', '.join(keys)
                reason = _("topology (%(topology)s) must have %(ks)s")
                raise exception.InvalidCPUInfo(reason=reason % locals())
            for key in keys:
                topology[key] = topology_node.get(key)

        feature_nodes = xml.findall('.//host/cpu/feature')
        features = list()
        for nodes in feature_nodes:
            features.append(nodes.get('name'))

        cpu_info['topology'] = topology
        cpu_info['features'] = features
        return utils.dumps(cpu_info)

    def block_stats(self, instance_name, disk):
        """
        Note that this function takes an instance name.
        """
        domain = self._lookup_by_name(instance_name)
        return domain.blockStats(disk)

    def interface_stats(self, instance_name, interface):
        """
        Note that this function takes an instance name.
        """
        domain = self._lookup_by_name(instance_name)
        return domain.interfaceStats(interface)

    def get_instance_disk_info(self, instance_name):
        """Preparation block migration.

        :params ctxt: security context
        :params instance_ref:
            nova.db.sqlalchemy.models.Instance object
            instance object that is migrated.
        :return:
            json strings with below format::

                "[{'path':'disk', 'type':'raw',
                  'virt_disk_size':'10737418240',
                  'backing_file':'backing_file',
                  'disk_size':'83886080'},...]"

        """
        disk_info = []

        virt_dom = self._lookup_by_name(instance_name)
        xml = virt_dom.XMLDesc(0)
        doc = ElementTree.fromstring(xml)
        disk_nodes = doc.findall('.//devices/disk')
        path_nodes = doc.findall('.//devices/disk/source')
        driver_nodes = doc.findall('.//devices/disk/driver')

        for cnt, path_node in enumerate(path_nodes):
            disk_type = disk_nodes[cnt].get('type')
            path = path_node.get('file')

            if disk_type != 'file':
                LOG.debug(_('skipping %(path)s since it looks like volume') %
                          locals())
                continue

            # get the real disk size or
            # raise a localized error if image is unavailable
            dk_size = int(os.path.getsize(path))

            disk_type = driver_nodes[cnt].get('type')
            if disk_type == "qcow2":
                out, err = utils.execute('qemu-img', 'info', path)

                # virtual size:
                size = [i.split('(')[1].split()[0] for i in out.split('\n')
                    if i.strip().find('virtual size') >= 0]
                virt_size = int(size[0])

                # backing file:(actual path:)
                backing_file = libvirt_utils.get_disk_backing_file(path)
            else:
                backing_file = ""
                virt_size = 0

            disk_info.append({'type': disk_type,
                              'path': path,
                              'virt_disk_size': virt_size,
                              'backing_file': backing_file,
                              'disk_size': dk_size})
        return utils.dumps(disk_info)

    def get_disk_available_least(self):
        """Return disk available least size.

        The size of available disk, when block_migration command given
        disk_over_commit param is FALSE.

        The size that deducted real nstance disk size from the total size
        of the virtual disk of all instances.

        """
        # available size of the disk
        dk_sz_gb = self.get_local_gb_total() - self.get_local_gb_used()

        # Disk size that all instance uses : virtual_size - disk_size
        instances_name = self.list_instances()
        instances_sz = 0
        for i_name in instances_name:
            try:
                disk_infos = utils.loads(self.get_instance_disk_info(i_name))
                for info in disk_infos:
                    i_vt_sz = int(info['virt_disk_size'])
                    i_dk_sz = int(info['disk_size'])
                    instances_sz += i_vt_sz - i_dk_sz
            except OSError as e:
                if e.errno == errno.ENOENT:
                    LOG.error(_("Getting disk size of %(i_name)s: %(e)s") %
                              locals())
                else:
                    raise
            except exception.InstanceNotFound:
                # Instance was deleted during the check so ignore it
                pass
            # NOTE(gtt116): give change to do other task.
            greenthread.sleep(0)
        # Disk available least size
        available_least_size = dk_sz_gb * (1024 ** 3) - instances_sz
        return (available_least_size / 1024 / 1024 / 1024)

    def update_host_status(self):
        """Retrieve status info from libvirt.

        Query libvirt to get the state of the compute node, such
        as memory and disk usage.
        """
        return self.host_state.update_status()

    def get_host_stats(self, refresh=False):
        """Return the current state of the host.

        If 'refresh' is True, run update the stats first."""
        return self.host_state.get_host_stats(refresh=refresh)


class HostState(object):
    """Manages information about the compute node through libvirt"""
    def __init__(self, read_only):
        super(HostState, self).__init__()
        self.read_only = read_only
        self._stats = {}
        self.connection = None
        self.update_status()

    def get_host_stats(self, refresh=False):
        """Return the current state of the host.

        If 'refresh' is True, run update the stats first."""
        if refresh:
            self.update_status()
        return self._stats

    def update_status(self):
        """Retrieve status info from libvirt."""
        LOG.debug(_("Updating host stats"))
        if self.connection is None:
            self.connection = get_connection(self.read_only)
        data = {}
        data["vcpus"] = self.connection.get_vcpu_total()
        data["vcpus_used"] = self.connection.get_vcpu_used()
        data["cpu_info"] = utils.loads(self.connection.get_cpu_info())
        data["disk_total"] = self.connection.get_local_gb_total()
        data["disk_used"] = self.connection.get_local_gb_used()
        data["disk_available"] = data["disk_total"] - data["disk_used"]
        data["host_memory_total"] = self.connection.get_memory_mb_total()
        data["host_memory_free"] = (data["host_memory_total"] -
                                    self.connection.get_memory_mb_used())
        data["hypervisor_type"] = self.connection.get_hypervisor_type()
        data["hypervisor_version"] = self.connection.get_hypervisor_version()

        self._stats = data

        return data


class LibvirtOpenVswitchDriver(vif.VIFDriver):
    """VIF driver for Open vSwitch that uses type='ethernet'
       libvirt XML.  Used for libvirt versions that do not support
       OVS virtual port XML (0.9.10 or earlier)."""

    def get_dev_name(_self, iface_id):
        return "tap" + iface_id[0:11]

    def plug(self, instance, network, mapping):
        iface_id = mapping['vif_uuid']
        dev = self.get_dev_name(iface_id)
        if not linux_net._device_exists(dev):
            # Older version of the command 'ip' from the iproute2 package
            # don't have support for the tuntap option (lp:882568).  If it
            # turns out we're on an old version we work around this by using
            # tunctl.
            try:
                # First, try with 'ip'
                utils.execute('ip', 'tuntap', 'add', dev, 'mode', 'tap',
                          run_as_root=True)
            except exception.ProcessExecutionError:
                # Second option: tunctl
                utils.execute('tunctl', '-b', '-t', dev, run_as_root=True)
            utils.execute('ip', 'link', 'set', dev, 'up', run_as_root=True)
        utils.execute('ovs-vsctl', '--', '--may-exist', 'add-port',
                FLAGS.libvirt_ovs_bridge, dev,
                '--', 'set', 'Interface', dev,
                "external-ids:iface-id=%s" % iface_id,
                '--', 'set', 'Interface', dev,
                "external-ids:iface-status=active",
                '--', 'set', 'Interface', dev,
                "external-ids:attached-mac=%s" % mapping['mac'],
                '--', 'set', 'Interface', dev,
                "external-ids:vm-uuid=%s" % instance['uuid'],
                run_as_root=True)

        result = {
            'script': '',
            'name': dev,
            'mac_address': mapping['mac']}
        return result

    def unplug(self, instance, network, mapping):
        """Unplug the VIF from the network by deleting the port from
        the bridge."""
        dev = self.get_dev_name(mapping['vif_uuid'])
        try:
            utils.execute('ovs-vsctl', 'del-port',
                          FLAGS.libvirt_ovs_bridge, dev, run_as_root=True)
            utils.execute('ip', 'link', 'delete', dev, run_as_root=True)
        except exception.ProcessExecutionError:
            LOG.exception(_("Failed while unplugging vif of instance '%s'"),
                        instance['name'])



