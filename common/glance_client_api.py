# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import absolute_import

import itertools
import thread

import glanceclient as glance_client


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
    copy_from = kwargs.pop('copy_from', None)
    data = kwargs.pop('data', None)

    image = glanceclient(url).images.create(**kwargs)

    if data:
        thread.start_new_thread(image_update,
                                (url, image.id),
                                {'data': data,
                                 'purge_props': False})
    elif copy_from:
        thread.start_new_thread(image_update,
                                (url, image.id),
                                {'copy_from': copy_from,
                                 'purge_props': False})
    return image
