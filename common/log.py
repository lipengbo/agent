#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:logging.py
# Date:Thu May 23 10:08:22 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import logging
import logging.config
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(module)s.%(funcName)s:%(lineno)d] [%(levelname)s]- %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '../logs/ceni_agent.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'standard',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'agent': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}


def mklogdir():
    import os
    if not os.path.exists('../logs'):
        os.mkdir('../logs')


def getLogger(name):
    mklogdir()
    logging.config.dictConfig(LOGGING)
    return logging.getLogger(name)
