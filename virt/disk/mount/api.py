#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:api.py
# Date:Mon Oct 21 11:03:58 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
"""Support for mounting virtual image files."""

import os
import time

from common.utils import import_object
from common import log as logging
from virt import utils

LOG = logging.getLogger('agent')

MAX_DEVICE_WAIT = 30


class Mount(object):

    """Standard mounting operations, that can be overridden by subclasses.

    The basic device operations provided are get, map and mount,
    to be called in that order.
    """

    mode = None  # to be overridden in subclasses

    @staticmethod
    def instance_for_format(imgfile, mountdir, partition, imgfmt):
        LOG.debug("Instance for format imgfile=%(imgfile)s mountdir=%(mountdir)s partition=%(partition)s imgfmt=%(imgfmt)s" %
                  {'imgfile': imgfile, 'mountdir': mountdir,
                   'partition': partition, 'imgfmt': imgfmt})
        if imgfmt == "raw":
            LOG.debug("Using LoopMount")
            return import_object(
                "virt.disk.mount.loop.LoopMount",
                imgfile, mountdir, partition)
        else:
            LOG.debug("Using NbdMount")
            return import_object(
                "virt.disk.mount.nbd.NbdMount",
                imgfile, mountdir, partition)

    @staticmethod
    def instance_for_device(imgfile, mountdir, partition, device):
        LOG.debug("Instance for device imgfile=%(imgfile)s mountdir=%(mountdir)s partition=%(partition)s device=%(device)s" %
                  {'imgfile': imgfile, 'mountdir': mountdir,
                   'partition': partition, 'device': device})
        if "loop" in device:
            LOG.debug("Using LoopMount")
            return import_object(
                "virt.disk.mount.loop.LoopMount",
                imgfile, mountdir, partition, device)
        else:
            LOG.debug("Using NbdMount")
            return import_object(
                "virt.disk.mount.nbd.NbdMount",
                imgfile, mountdir, partition, device)

    def __init__(self, image, mount_dir, partition=None, device=None):

        # Input
        self.image = image
        self.partition = partition
        self.mount_dir = mount_dir

        # Output
        self.error = ""

        # Internal
        self.linked = self.mapped = self.mounted = self.automapped = False
        self.device = self.mapped_device = device

        # Reset to mounted dir if possible
        self.reset_dev()

    def reset_dev(self):
        """Reset device paths to allow unmounting."""
        if not self.device:
            return

        self.linked = self.mapped = self.mounted = True

        device = self.device
        if os.path.isabs(device) and os.path.exists(device):
            if device.startswith('/dev/mapper/'):
                device = os.path.basename(device)
                device, self.partition = device.rsplit('p', 1)
                self.device = os.path.join('/dev', device)

    def get_dev(self):
        """Make the image available as a block device in the file system."""
        self.device = None
        self.linked = True
        return True

    def _get_dev_retry_helper(self):
        """Some implementations need to retry their get_dev."""
        # simply calls _get_dev_retry_helper from their get_dev, and implements
        # _inner_get_dev with their device acquisition logic. The NBD
        # implementation has an example.
        start_time = time.time()
        device = self._inner_get_dev()
        while not device:
            LOG.info("Device allocation failed. Will retry in 2 seconds.")
            time.sleep(2)
            if time.time() - start_time > MAX_DEVICE_WAIT:
                LOG.warn("Device allocation failed after repeated retries.")
                return False
            device = self._inner_get_dev()
        return True

    def _inner_get_dev(self):
        raise NotImplementedError()

    def unget_dev(self):
        """Release the block device from the file system namespace."""
        self.linked = False

    def map_dev(self):
        """Map partitions of the device to the file system namespace."""
        assert(os.path.exists(self.device))
        LOG.debug("Map dev %s" % self.device)
        automapped_path = '/dev/%sp%s' % (os.path.basename(self.device), self.partition)

        if self.partition == -1:
            self.error = "partition search unsupported with %s" % self.mode
        elif self.partition and not os.path.exists(automapped_path):
            map_path = '/dev/mapper/%sp%s' % (os.path.basename(self.device), self.partition)
            assert(not os.path.exists(map_path))

            # Note kpartx can output warnings to stderr and succeed
            # Also it can output failures to stderr and "succeed"
            # So we just go on the existence of the mapped device
            _out, err = utils.trycmd('kpartx', '-a', self.device,
                                     run_as_root=True, discard_warnings=True)

            # Note kpartx does nothing when presented with a raw image,
            # so given we only use it when we expect a partitioned image, fail
            if not os.path.exists(map_path):
                if not err:
                    err = "partition %s not found" % self.partition
                self.error = "Failed to map partitions: %s" % err
            else:
                self.mapped_device = map_path
                self.mapped = True
        elif self.partition and os.path.exists(automapped_path):
            # Note auto mapping can be enabled with the 'max_part' option
            # to the nbd or loop kernel modules. Beware of possible races
            # in the partition scanning for _loop_ devices though
            # (details in bug 1024586), which are currently uncatered for.
            self.mapped_device = automapped_path
            self.mapped = True
            self.automapped = True
        else:
            self.mapped_device = self.device
            self.mapped = True

        return self.mapped

    def unmap_dev(self):
        """Remove partitions of the device from the file system namespace."""
        if not self.mapped:
            return
        LOG.debug("Unmap dev %s" % self.device)
        if self.partition and not self.automapped:
            utils.execute('kpartx', '-d', self.device, run_as_root=True)
        self.mapped = False
        self.automapped = False

    def mnt_dev(self):
        """Mount the device into the file system."""
        LOG.debug("Mount %(dev)s on %(dir)s" %
                  {'dev': self.mapped_device, 'dir': self.mount_dir})
        _out, err = utils.trycmd('mount', self.mapped_device, self.mount_dir,
                                 discard_warnings=True, run_as_root=True)
        if err:
            self.error = "Failed to mount filesystem: %s" % err
            LOG.debug(self.error)
            return False

        self.mounted = True
        return True

    def unmnt_dev(self):
        """Unmount the device from the file system."""
        if not self.mounted:
            return
        LOG.debug("Umount %s" % self.mapped_device)
        utils.execute('umount', self.mapped_device, run_as_root=True)
        self.mounted = False

    def do_mount(self):
        """Call the get, map and mnt operations."""
        status = False
        try:
            status = self.get_dev() and self.map_dev() and self.mnt_dev()
        finally:
            if not status:
                LOG.debug("Fail to mount, tearing back down")
                LOG.error(self.error)
                self.do_teardown()
        return status

    def do_umount(self):
        """Call the unmnt operation."""
        if self.mounted:
            self.unmnt_dev()

    def do_teardown(self):
        """Call the umnt, unmap, and unget operations."""
        if self.mounted:
            self.unmnt_dev()
        if self.mapped:
            self.unmap_dev()
        if self.linked:
            self.unget_dev()
