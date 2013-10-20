#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:utils.py
# Date:Sat Oct 19 19:26:34 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
from common import utils


def execute(*args, **kwargs):
    return utils.execute(shell=False, *args, **kwargs)


def get_fs_info(path):
    """Get free/used/total space info for a filesystem

    :param path: Any dirent on the filesystem
    :returns: A dict containing:

             :free: How much space is free (in bytes)
             :used: How much space is used (in bytes)
             :total: How big the filesystem is (in bytes)
    """
    hddinfo = os.statvfs(path)
    total = hddinfo.f_frsize * hddinfo.f_blocks
    free = hddinfo.f_frsize * hddinfo.f_bavail
    used = hddinfo.f_frsize * (hddinfo.f_blocks - hddinfo.f_bfree)
    return {'total': total,
            'free': free,
            'used': used}


def get_disk_backing_file(path):
    """Get the backing file of a disk image

    :param path: Path to the disk image
    :returns: a path to the image's backing store
    """
    out, err = execute('qemu-img', 'info', path)
    backing_file = None

    for line in out.split('\n'):
        if line.startswith('backing file: '):
            if 'actual path: ' in line:
                backing_file = line.split('actual path: ')[1][:-1]
            else:
                backing_file = line.split('backing file: ')[1]
            break
    if backing_file:
        backing_file = os.path.basename(backing_file)

    return backing_file


def create_cow_image(backing_file, path, size_gb):
    """Create COW image

    Creates a COW image with the given backing file

    :param backing_file: Existing image on which to base the COW image
    :param path: Desired location of the COW image
    """
    size = '%sG' % size_gb
    execute('qemu-img', 'create', '-f', 'qcow2', '-o', 'backing_file=%s' % backing_file, path, size)
