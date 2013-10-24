#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:images.py
# Date:Thu Oct 24 13:30:50 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from virt.images import fetch
#from virt import utils


def test_fetch():
    url = 'http://192.168.5.107:9292/v1/images/53807c3b-8d25-4d4f-9249-a798ce0b7013'
    target_file = '/var/lib/libvirt/images/53807c3b-8d25-4d4f-9249-a798ce0b7013'
    out, err = fetch(url, target_file)
    #out, err = utils.trycmd('curl', '--fail', url, '-o', target_file, discard_warnings=True)
    #out, err = utils.trycmd('wget', url, '-O', target_file, discard_warnings=True)
    #out, err = utils.trycmd('wget', '-O', target_file, url, discard_warnings=True)
    print out
    print '-------------------------------------------'
    print err
