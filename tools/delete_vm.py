#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:delete_vm.py
# Date:二 12月 24 09:38:24 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import sys
sys.path.insert(0, '../')
from service.compute import ComputeManager


if __name__ == '__main__':
    argvs = sys.argv
    print argvs
    if len(argvs) < 2:
        print 'usage: python delete_vm.py vm_uuid1 vm_uuid2'
    else:
        manager = ComputeManager()
        for vname in argvs[1:]:
            manager.delete_domain(vname)
