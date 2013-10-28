#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:test.py
# Date:Sat Oct 19 15:13:25 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import sys


if __name__ == '__main__':
    module_name, sep, function_name = sys.argv[1].rpartition('.')
    module_name = 'tests.' + module_name
    if module_name not in sys.modules:
        __import__(module_name)
    print getattr(sys.modules[module_name], function_name)()
