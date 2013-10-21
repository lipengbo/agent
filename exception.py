#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:exception.py
# Date:Mon Oct 21 23:59:33 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from common import log as logging
LOG = logging.getLogger("agent.virt")


class AgentException(Exception):
    """Base Agent Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception:
                LOG.exception('Exception in string format operation')
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))
                message = self.msg_fmt
        super(AgentException, self).__init__(message)

    def format_message(self):
        if self.__class__.__name__.endswith('_Remote'):
            return self.args[0]
        else:
            return unicode(self)


class DownloadImageException(AgentException):
    msg_fmt = "Failed to download image: %(image_uuid)s"


class CreateImageException(AgentException):
    msg_fmt = "Create Image Error for vm: %(instance_id)s"


class VirtualInterfaceException(AgentException):
    msg_fmt = "Plug virtual interface failed for vm: %(instance_id)s"
