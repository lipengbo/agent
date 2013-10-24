#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:utils.py
# Date:Sat Oct 19 19:26:34 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
from common import utils


def execute(*args, **kwargs):
    kwargs['shell'] = kwargs.get('shell', False)
    return utils.execute(*args, **kwargs)


def trycmd(*args, **kwargs):
    kwargs['shell'] = kwargs.get('shell', False)
    return utils.trycmd(*args, **kwargs)


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
