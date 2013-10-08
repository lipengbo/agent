#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:images.py
# Date:Mon May 27 21:25:23 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
"""
Utility methods to resize, repartition, and modify disk images.

Includes injection of SSH keys into authorized_keys file,and

network interface file

"""

import os
import tempfile
import time
from libs import excutils
from libs import exception
from etc import config
import traceback
from libs import log as logging
LOG = logging.getLogger("agent.image")


def fetch_image(glanceURL, imageUUID):
    image = os.path.join(config.image_path, imageUUID)
    if not os.path.exists(image):
        out, err = excutils.execute("wget -O %s %s" % (image, glanceURL))
        if err:
            return None
    return image


def create_image(glanceURL, imageUUID, vname, size, dhcp=1, net=None, key=None):
    image = fetch_image(glanceURL, imageUUID)
    if image:
        instance_path = os.path.join(config.image_path, vname)
        instance_image = os.path.join(config.image_path, vname, imageUUID)
        try:
            excutils.execute("mkdir -p %s" % instance_path)
            excutils.execute("qemu-img create -f qcow2 -o backing_file=%s %s" % (image, instance_image))
            if not dhcp:
                try:
                    inject_data(instance_image, net=net, key=key)
                except:
                    # try it again
                    time.sleep(1)
                    inject_data(instance_image, net=net, key=key)
            return True
        except:
            LOG.error(traceback.print_exc())
            excutils.execute("rm -rf %s" % instance_path)
    return False


def delete_image(vname):
    instance_path = os.path.join(config.image_path, vname)
    if os.path.exists(instance_path):
        excutils.execute("rm -rf  %s" % instance_path)


def extend(image, size):
    """Increase image to size"""
    file_size = os.path.getsize(image)
    if file_size >= size:
        return
    excutils.execute('truncate -s %s %s' % (size, image))
    # NOTE(vish): attempts to resize filesystem
    excutils.execute('e2fsck -fp %s' % image, check_exit_code=False)
    excutils.execute('resize2fs %s' % image, check_exit_code=False)


NBD_MAX = 16
_DEVICES = ['/dev/nbd%s' % i for i in xrange(NBD_MAX)]


def inject_data(image, key=None, net=None, partition=None, nbd=True):
    """Injects a ssh key and optionally net data into a disk image.

    it will mount the image as a fully partitioned disk and attempt to inject
    into the specified partition number.

    If partition is not specified it mounts the image as a single partition.

    """
    device = _link_device(image, nbd)
    try:
        if partition:
            out, err = excutils.execute('sudo kpartx -a %s' % device)
            if err:
                raise exception.Error('Failed to load partition: %s' % err)
            mapped_device = '/dev/mapper/%sp%s' % (device.split('/')[-1],
                                                   partition)
        else:
            mapped_device = '%sp1' % device
        if not os.path.exists(mapped_device):
            raise exception.Error(
                'Mapped device was not found : %s' % mapped_device)
        tmpdir = tempfile.mkdtemp()
        try:
            # mount loopback to dir
            out, err = excutils.execute(
                'sudo mount %s %s' % (mapped_device, tmpdir))
            if err:
                raise exception.Error('Failed to mount filesystem: %s' % err)

            try:
                if key:
                    # inject key file
                    _inject_key_into_fs(key, tmpdir)
                if net:
                    _inject_net_into_fs(net, tmpdir)
            finally:
                # unmount device
                excutils.execute('sudo umount %s' % mapped_device)
        finally:
            # remove temporary directory
            excutils.execute('rmdir %s' % tmpdir)
            if not partition is None:
                # remove partitions
                excutils.execute('sudo kpartx -d %s' % device)
    finally:
        _unlink_device(device, nbd)


def _link_device(image, nbd):
    """Link image to device using loopback or nbd"""
    if nbd:
        device = _allocate_device()
        excutils.execute('modprobe nbd max_part=%s' % NBD_MAX)
        excutils.execute('sudo qemu-nbd -c %s %s' % (device, image))
        for i in xrange(10):
            if os.path.exists("/sys/block/%s/pid" % os.path.basename(device)):
                return device
            time.sleep(1)
        raise exception.Error('nbd device %s did not show up' % device)
    else:
        out, err = excutils.execute('sudo losetup --find --show %s' % image)
        if err:
            raise exception.Error('Could not attach image to loopback: %s'
                                  % err)
        return out.strip()


def _unlink_device(device, nbd):
    """Unlink image from device using loopback or nbd"""
    if nbd:
        excutils.execute('sudo qemu-nbd -d %s' % device)
        _free_device(device)
    else:
        excutils.execute('sudo losetup --detach %s' % device)


def _allocate_device():
    while True:
        if not _DEVICES:
            raise exception.Error('No free nbd devices')
        device = _DEVICES.pop()
        if not os.path.exists("/sys/block/%s/pid" % os.path.basename(device)):
            break
    return device


def _free_device(device):
    _DEVICES.append(device)


def _inject_key_into_fs(key, fs):
    """Add the given public ssh key to root's authorized_keys.

    key is an ssh key string.
    fs is the path to the base of the filesystem into which to inject the key.
    """
    sshdir = os.path.join(fs, 'root', '.ssh')
    excutils.execute('sudo mkdir -p %s' %
                     sshdir)  # existing dir doesn't matter
    excutils.execute('sudo chown root %s' % sshdir)
    excutils.execute('sudo chmod 700 %s' % sshdir)
    keyfile = os.path.join(sshdir, 'authorized_keys')
    excutils.execute('sudo tee -a %s' % keyfile, '\n' + key.strip() + '\n')


def _inject_net_into_fs(net, fs):
    """Inject /etc/network/interfaces into the filesystem rooted at fs.

    net is the contents of /etc/network/interfaces.
    """
    netdir = os.path.join(os.path.join(fs, 'etc'), 'network')
    excutils.execute('sudo mkdir -p %s' %
                     netdir)  # existing dir doesn't matter
    excutils.execute('sudo chown root:root %s' % netdir)
    excutils.execute('sudo chmod 755 %s' % netdir)
    netfile = os.path.join(netdir, 'interfaces')
    excutils.execute('sudo tee %s' % netfile, net)
