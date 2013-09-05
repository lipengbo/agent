#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:exception.py
# Date:Tue May 21 13:09:53 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com


class Error(Exception):

    def __init__(self, message=None):
        super(Error, self).__init__(message)


class TimeoutException(Error):
    pass


class ActionError(Error):
    pass


class CreateImageError(Error):
    pass


class PrepareLinkError(Error):
    pass


def wrap_exception(f):
    def _wrap(*args, **kw):
        try:
            return f(*args, **kw)
        except Exception:
            raise
    _wrap.func_name = f.func_name
    return _wrap
