#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:loop.py
# Date:Mon Oct 21 11:19:46 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
"""Support for mounting images with the loop device."""

from common import log as logging
from virt import utils
from virt.disk.mount import api

LOG = logging.getLogger('agent')


class LoopMount(api.Mount):

    """loop back support for raw images."""
    mode = 'loop'

    def _inner_get_dev(self):
        out, err = utils.trycmd('losetup', '--find', '--show', self.image,
                                run_as_root=True)
        if err:
            self.error = "Could not attach image to loopback: %s" % err
            LOG.info("Loop mount error: %s" % self.error)
            self.linked = False
            self.device = None
            return False

        self.device = out.strip()
        LOG.debug("Got loop device %s" % self.device)
        self.linked = True
        return True

    def get_dev(self):
        # devices. Note however that modern kernels will use more loop devices
        # if they exist. If you're seeing lots of retries, consider adding
        # more devices.
        return self._get_dev_retry_helper()

    def unget_dev(self):
        if not self.linked:
            return

        # thus leaking a loop device unless the losetup --detach is retried:
        # https://lkml.org/lkml/2012/9/28/62
        LOG.debug("Release loop device %s" % self.device)
        utils.execute('losetup', '--detach', self.device, run_as_root=True,
                      attempts=3)
        self.linked = False
        self.device = None
