#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:nbd.py
# Date:Mon Oct 21 11:19:57 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
"""Support for mounting images with qemu-nbd."""

import os
import random
import re
import time
from common import log as logging
from virt import utils
from virt.disk.mount import api
LOG = logging.getLogger('agent')
NBD_DEVICE_RE = re.compile('nbd[0-9]+')
TIMEOUT_NBD = 10


class NbdMount(api.Mount):

    """qemu-nbd support disk images."""
    mode = 'nbd'

    def _detect_nbd_devices(self):
        """Detect nbd device files."""
        return filter(NBD_DEVICE_RE.match, os.listdir('/sys/block/'))

    def _find_unused(self, devices):
        for device in devices:
            if not os.path.exists(os.path.join('/sys/block/', device, 'pid')):
                return device
        LOG.warn("No free nbd devices")
        return None

    def _allocate_nbd(self):
        if not os.path.exists('/sys/block/nbd0'):
            LOG.error("nbd module not loaded")
            self.error = 'nbd unavailable: module not loaded'
            _out, err = utils.trycmd('modprobe', 'nbd', 'max_part=63')
            if err:
                LOG.error(err)
            return None

        devices = self._detect_nbd_devices()
        random.shuffle(devices)
        device = self._find_unused(devices)
        if not device:
            # really want to log this info, not raise
            self.error = 'No free nbd devices'
            return None
        return os.path.join('/dev', device)

    def _read_pid_file(self, pidfile):
        # This is for unit test convenience
        with open(pidfile) as f:
            pid = int(f.readline())
        return pid

    def _inner_get_dev(self):
        device = self._allocate_nbd()
        if not device:
            return False

        # NOTE(mikal): qemu-nbd will return an error if the device file is
        # already in use.
        LOG.debug("Get nbd device %(dev)s for %(imgfile)s" %
                  {'dev': device, 'imgfile': self.image})
        _out, err = utils.trycmd('qemu-nbd', '-c', device, self.image,
                                 run_as_root=True)
        if err:
            self.error = "qemu-nbd error: %s" % err
            LOG.info("NBD mount error: %s" % self.error)
            return False

        # NOTE(vish): this forks into another process, so give it a chance
        # to set up before continuing
        pidfile = "/sys/block/%s/pid" % os.path.basename(device)
        for _i in range(TIMEOUT_NBD):
            if os.path.exists(pidfile):
                self.device = device
                break
            time.sleep(1)
        else:
            self.error = "nbd device %s did not show up" % device
            LOG.info("NBD mount error: %s" % self.error)

            # Cleanup
            _out, err = utils.trycmd('qemu-nbd', '-d', device,
                                     run_as_root=True)
            if err:
                LOG.warn(
                    "Detaching from erroneous nbd device returned error: %s" % err)
            return False

        self.error = ''
        self.linked = True
        return True

    def get_dev(self):
        """Retry requests for NBD devices."""
        return self._get_dev_retry_helper()

    def unget_dev(self):
        if not self.linked:
            return
        LOG.debug("Release nbd device %s" % self.device)
        utils.execute('qemu-nbd', '-d', self.device, run_as_root=True)
        self.linked = False
        self.device = None
