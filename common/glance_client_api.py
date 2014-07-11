#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:glance_client_api.py
# Date:四  6月 26 11:08:20 CST 2014
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from __future__ import absolute_import

import itertools
#import thread

from common import glanceclient as glance_client


def glanceclient(url):
    return glance_client.Client('1', url)


def image_delete(url, image_id):
    return glanceclient(url).images.delete(image_id)


def image_get(url, image_id):
    """Returns an Image object populated with metadata for image
    with supplied identifier.
    """
    image = glanceclient(url).images.get(image_id)
    if not hasattr(image, 'name'):
        image.name = None
    return image


def image_list_detailed(url, marker=None, filters=None, paginate=False):
    limit = 1000
    page_size = 100

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {'filters': filters or {}}
    if marker:
        kwargs['marker'] = marker

    images_iter = glanceclient(url).images.list(page_size=request_size,
                                                limit=limit,
                                                **kwargs)
    has_more_data = False
    if paginate:
        images = list(itertools.islice(images_iter, request_size))
        if len(images) > page_size:
            images.pop(-1)
            has_more_data = True
    else:
        images = list(images_iter)
    return (images, has_more_data)


def image_update(url, image_id, **kwargs):
    return glanceclient(url).images.update(image_id, **kwargs)


def image_create(url, **kwargs):
    location = kwargs.pop('location', None)
    data = kwargs.pop('data', None)

    image = glanceclient(url).images.create(**kwargs)

    if data:
        image_update(url, image.id, {'data': data, 'purge_props': False})
    elif location:
        image_update(url, image.id, {'location': location, 'purge_props': False})
    return image
