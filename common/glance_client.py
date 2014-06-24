#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:glance.py
# Date:二  6月 24 16:16:07 CST 2014
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import functools
import gettext
import optparse
import os
import sys
import time
import warnings
from urlparse import urlparse

# If ../glance/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'glance', '__init__.py')):
    sys.path.insert(0, possible_topdir)

gettext.install('glance', unicode=1)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from glance import client as glance_client

from glance.common import exception
from glance.common import utils
from glance.version import version_info as version


SUCCESS = 0
FAILURE = 1

DEFAULT_PORT = 9292


# TODO(sirp): make more of the actions use this decorator
def catch_error(action):
    """Decorator to provide sensible default error handling for actions."""
    def wrap(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                ret = func(*args, **kwargs)
                return SUCCESS if ret is None else ret
            except exception.Forbidden:
                print ("Not authorized to make this request. Check "
                       "your credentials (OS_AUTH_USER, OS_AUTH_KEY, ...).")
                return FAILURE
            except exception.ClientConfigurationError:
                raise
            except Exception as e:
                options = args[0]
                if options.debug:
                    raise
                print "Failed to %s. Got error:" % action
                pieces = unicode(e).split('\n')
                for piece in pieces:
                    print piece
                return FAILURE

        return wrapper
    return wrap


def get_image_fields_from_args(args):
    """
    Validate the set of arguments passed as field name/value pairs
    and return them as a mapping.
    """
    fields = {}
    for arg in args:
        pieces = arg.strip(',').split('=')
        if len(pieces) != 2:
            msg = ("Arguments should be in the form of field=value. "
                   "You specified %s." % arg)
            raise RuntimeError(msg)
        fields[pieces[0]] = pieces[1]

    return fields


def get_image_filters_from_args(args):
    """Build a dictionary of query filters based on the supplied args."""
    try:
        fields = get_image_fields_from_args(args)
    except RuntimeError as e:
        print e
        return FAILURE

    SUPPORTED_FILTERS = ['name', 'disk_format', 'container_format', 'status',
                         'min_ram', 'min_disk', 'size_min', 'size_max',
                         'changes-since']
    filters = {}
    for (key, value) in fields.items():
        if key not in SUPPORTED_FILTERS:
            key = 'property-%s' % (key,)
        filters[key] = value

    return filters


def print_image_formatted(client, image):
    """
    Formatted print of image metadata.

    :param client: The Glance client object
    :param image: The image metadata
    """
    print "URI: %s://%s:%s/v1/images/%s" % (
        client.use_ssl and "https" or "http",
                                      client.host,
                                      client.port,
                                      image['id'])
    print "Id: %s" % image['id']
    print "Public: " + (image['is_public'] and "Yes" or "No")
    print "Protected: " + (image['protected'] and "Yes" or "No")
    print "Name: %s" % image['name']
    print "Status: %s" % image['status']
    print "Size: %d" % int(image['size'])
    print "Disk format: %s" % image['disk_format']
    print "Container format: %s" % image['container_format']
    print "Minimum Ram Required (MB): %s" % image['min_ram']
    print "Minimum Disk Required (GB): %s" % image['min_disk']
    if image.get('owner'):
        print "Owner: %s" % image['owner']
    if len(image['properties']) > 0:
        for k, v in image['properties'].items():
            print "Property '%s': %s" % (k, v)
    print "Created at: %s" % image['created_at']
    if image.get('deleted_at'):
        print "Deleted at: %s" % image['deleted_at']
    if image.get('updated_at'):
        print "Updated at: %s" % image['updated_at']


def image_add(options, args):
    """
%(prog)s add [options] <field1=value1 field2=value2 ...> [ < /path/to/image ]

Adds a new image to Glance. Specify metadata fields as arguments.

SPECIFYING IMAGE METADATA
===============================================================================

All field/value pairs are converted into a mapping that is passed
to Glance that represents the metadata for an image.

Field names of note:

id                  Optional. If not specified, an image identifier will be
                    automatically assigned.
name                Optional. A name for the image.
size                Optional. Should be size in bytes of the image if
                    specified.
is_public           Optional. If specified, interpreted as a boolean value
                    and sets or unsets the image's availability to the public.
                    The default value is False.
protected           Optional. If specified, interpreted as a boolean value
                    and enables or disables deletion protection.
                    The default value is False.
min_disk            Optional. The minimum disk size in gigabytes required to
                    boot the image. If unspecified, this value defaults to 0
                    (no minimum).
min_ram             Optional. The minimum ram size in megabytes required to
                    boot the image. If unspecified, this value defaults to 0
                    (no minimum).
disk_format         Required. If unspecified and container_format is specified
                    as 'ami', 'ari' or 'aki', disk_format will default to the
                    container_format value. Possible values are 'ami', 'ari',
                    'aki', 'vhd', 'vmk', 'raw', 'qcow2' and 'vdi'.
container_format    Required. If unspecified and disk_format is specified as
                    'ami', 'ari' or 'aki', container_format will default to the
                    disk_format value. Possible values are 'ami', 'ari', 'aki',
                    'bare' and 'ovf'.
location            Optional. When specified, should be a readable location
                    in the form of a URI: $STORE://LOCATION. For example, if
                    the image data is stored in a file on the local
                    filesystem at /usr/share/images/some.image.tar.gz
                    you would specify:
                    location=file:///usr/share/images/some.image.tar.gz
copy_from           Optional. An external location (HTTP, S3 or Swift URI) to
                    copy image content from. For example, if the image data is
                    stored as an object called fedora16 in an S3 bucket named
                    images, you would specify (with the approriate access and
                    secret keys):
                    copy_from=s3://akey:skey@s3.amazonaws.com/images/fedora16

Any other field names are considered to be custom properties so be careful
to spell field names correctly.

STREAMING IMAGE DATA
===============================================================================

If the location field is not specified, you can stream an image file on
the command line using standard redirection. For example:

%(prog)s add name="Ubuntu 10.04 LTS 5GB" < /tmp/images/myimage.tar.gz

EXAMPLES
===============================================================================

%(prog)s add name="My Image" disk_format=raw container_format=ovf \
    location=http://images.ubuntu.org/images/lucid-10.04-i686.iso \
    distro="Ubuntu 10.04 LTS"

%(prog)s add name="My Image" disk_format=raw container_format=ovf \
    distro="Ubuntu 10.04 LTS" < /tmp/myimage.iso"""
    c = get_client(options)

    try:
        fields = get_image_fields_from_args(args)
    except RuntimeError as e:
        print e
        return FAILURE

    image_meta = {'id': fields.pop('id', None),
                  'name': fields.pop('name', None),
                  'is_public': utils.bool_from_string(
                      fields.pop('is_public', False)),
                  'protected': utils.bool_from_string(
                      fields.pop('protected', False)),
                  'min_disk': fields.pop('min_disk', 0),
                  'min_ram': fields.pop('min_ram', 0),
                  }

    for format in ['disk_format', 'container_format']:
        if format in fields:
            image_meta[format] = fields.pop(format)

    # Strip any args that are not supported
    unsupported_fields = ['status', 'size']
    for field in unsupported_fields:
        if field in fields.keys():
            print 'Found non-settable field %s. Removing.' % field
            fields.pop(field)

    def _external_source(fields, image_data):
        source = None
        features = {}
        if 'location' in fields.keys():
            source = fields.pop('location')
            image_meta['location'] = source
            if 'checksum' in fields.keys():
                image_meta['checksum'] = fields.pop('checksum')
        elif 'copy_from' in fields.keys():
            source = fields.pop('copy_from')
            features['x-glance-api-copy-from'] = source
        return source, features

    # We need either a location or image data/stream to add...
    location, features = _external_source(fields, image_meta)
    image_data = None
    if not location:
        # Grab the image data stream from stdin or redirect,
        # otherwise error out
        image_data = sys.stdin

    # allow owner to be set when image is created
    if 'owner' in fields.keys():
        image_meta['owner'] = fields.pop('owner')

    # Add custom attributes, which are all the arguments remaining
    image_meta['properties'] = fields

    if not options.dry_run:
        try:
            image_meta = c.add_image(image_meta, image_data,
                                     features=features)
            image_id = image_meta['id']
            print "Added new image with ID: %s" % image_id
            if options.verbose:
                print "Returned the following metadata for the new image:"
                for k, v in sorted(image_meta.items()):
                    print " %(k)30s => %(v)s" % locals()
        except exception.ClientConnectionError as e:
            host = options.host
            port = options.port
            print ("Failed to connect to the Glance API server "
                   "%(host)s:%(port)d. Is the server running?" % locals())
            if options.verbose:
                pieces = unicode(e).split('\n')
                for piece in pieces:
                    print piece
            return FAILURE
        except Exception as e:
            print "Failed to add image. Got error:"
            pieces = unicode(e).split('\n')
            for piece in pieces:
                print piece
            print ("Note: Your image metadata may still be in the registry, "
                   "but the image's status will likely be 'killed'.")
            return FAILURE
    else:
        print "Dry run. We would have done the following:"

        def _dump(dict):
            for k, v in sorted(dict.items()):
                print " %(k)30s => %(v)s" % locals()

        print "Add new image with metadata:"
        _dump(image_meta)

        if features:
            print "with features enabled:"
            _dump(features)

    return SUCCESS


def image_update(options, args):
    """
%(prog)s update [options] <ID> <field1=value1 field2=value2 ...>

Updates an image's metadata in Glance. Specify metadata fields as arguments.

Metadata fields that are not specified in the update command will be deleted.

All field/value pairs are converted into a mapping that is passed
to Glance that represents the metadata for an image.

Field names that can be specified:

name                A name for the image.
location            An external location to serve out from.
copy_from           An external location (HTTP, S3 or Swift URI) to copy image
                    content from.
is_public           If specified, interpreted as a boolean value
                    and sets or unsets the image's availability to the public.
protected           If specified, interpreted as a boolean value
                    and enables or disables deletion protection for the image.
disk_format         Format of the disk image
container_format    Format of the container
min_disk            If specified, gives the minimum number of gigabytes of
                    space a disk must have to successfully boot the image.
min_ram             If specified, gives the minimum number of megabytes of
                    ram required to successfully boot the image.

All other field names are considered to be custom properties so be careful
to spell field names correctly."""
    c = get_client(options)
    try:
        image_id = args.pop(0)
    except IndexError:
        print "Please specify the ID of the image you wish to update "
        print "as the first argument"
        return FAILURE

    try:
        fields = get_image_fields_from_args(args)
    except RuntimeError as e:
        print e
        return FAILURE

    image_meta = {}

    # Strip any args that are not supported
    nonmodifiable_fields = ['created_on', 'deleted_on', 'deleted',
                            'updated_on', 'size', 'status']
    for field in nonmodifiable_fields:
        if field in fields.keys():
            print 'Found non-modifiable field %s. Removing.' % field
            fields.pop(field)

    features = {}
    if 'location' not in fields and 'copy_from' in fields:
        source = fields.pop('copy_from')
        features['x-glance-api-copy-from'] = source

    base_image_fields = ['disk_format', 'container_format', 'name',
                         'min_disk', 'min_ram', 'location', 'owner']
    for field in base_image_fields:
        fvalue = fields.pop(field, None)
        if fvalue is not None:
            image_meta[field] = fvalue

    # Have to handle "boolean" values specially...
    if 'is_public' in fields:
        image_meta['is_public'] = utils.bool_from_string(
            fields.pop('is_public'))
    if 'protected' in fields:
        image_meta['protected'] = utils.bool_from_string(
            fields.pop('protected'))

    # Add custom attributes, which are all the arguments remaining
    image_meta['properties'] = fields

    if not options.dry_run:
        try:
            image_meta = c.update_image(image_id, image_meta=image_meta,
                                        features=features)
            print "Updated image %s" % image_id

            if options.verbose:
                print "Updated image metadata for image %s:" % image_id
                print_image_formatted(c, image_meta)
        except exception.NotFound:
            print "No image with ID %s was found" % image_id
            return FAILURE
        except exception.Forbidden:
            print "You do not have permission to update image %s" % image_id
            return FAILURE
        except Exception as e:
            print "Failed to update image. Got error:"
            pieces = unicode(e).split('\n')
            for piece in pieces:
                print piece
            return FAILURE
    else:
        def _dump(dict):
            for k, v in sorted(dict.items()):
                print " %(k)30s => %(v)s" % locals()

        print "Dry run. We would have done the following:"
        print "Update existing image with metadata:"
        _dump(image_meta)

        if features:
            print "with features enabled:"
            _dump(features)

    return SUCCESS


def image_delete(options, args):
    """
%(prog)s delete [options] <ID>

Deletes an image from Glance"""
    try:
        image_id = args.pop()
    except IndexError:
        print "Please specify the ID of the image you wish to delete "
        print "as the first argument"
        return FAILURE

    if not (options.force or
            user_confirm("Delete image %s?" % (image_id,), default=False)):
        print 'Not deleting image %s' % (image_id,)
        return FAILURE

    c = get_client(options)

    try:
        c.delete_image(image_id)
        print "Deleted image %s" % image_id
        return SUCCESS
    except exception.NotFound:
        print "No image with ID %s was found" % image_id
        return FAILURE
    except exception.Forbidden:
        print "You do not have permission to delete image %s" % image_id
        return FAILURE


def image_show(options, args):
    """
%(prog)s show [options] <ID>

Shows image metadata for an image in Glance"""
    c = get_client(options)
    try:
        if len(args) > 0:
            image_id = args[0]
        else:
            print "Please specify the image identifier as the "
            print "first argument. Example: "
            print "$> glance-admin show 12345"
            return FAILURE

        image = c.get_image_meta(image_id)
        print_image_formatted(c, image)
        return SUCCESS
    except exception.NotFound:
        print "No image with ID %s was found" % image_id
        return FAILURE
    except Exception as e:
        print "Failed to show image. Got error:"
        pieces = unicode(e).split('\n')
        for piece in pieces:
            print piece
        return FAILURE


def _images_index(client, filters, limit, print_header=False, **kwargs):
    """Driver function for images_index"""
    parameters = {
        "filters": filters,
        "limit": limit,
    }

    optional_kwargs = ['marker', 'sort_key', 'sort_dir']
    for kwarg in optional_kwargs:
        if kwarg in kwargs:
            parameters[kwarg] = kwargs[kwarg]

    images = client.get_images(**parameters)

    if not images:
        return SUCCESS

    pretty_table = utils.PrettyTable()
    pretty_table.add_column(36, label="ID")
    pretty_table.add_column(30, label="Name")
    pretty_table.add_column(20, label="Disk Format")
    pretty_table.add_column(20, label="Container Format")
    pretty_table.add_column(14, label="Size", just="r")

    if print_header:
        print pretty_table.make_header()

    for image in images:
        print pretty_table.make_row(image['id'],
                                    image['name'],
                                    image['disk_format'],
                                    image['container_format'],
                                    image['size'])

    # suppress pagination when output is redirected
    suppress_pagination = (options.force or
                          (getattr(os, 'isatty') and not os.isatty(sys.stdout.fileno())))

    if not (suppress_pagination or len(images) != limit or
            user_confirm("Fetch next page?", True)):
        return SUCCESS

    parameters['marker'] = images[-1]['id']
    return _images_index(client, **parameters)


@catch_error('show index')
def images_index(options, args):
    """
%(prog)s index [options] <field1=value1 field2=value2 ...>

Returns basic information for all public images
a Glance server knows about. Provided fields are
handled as query filters. Supported filters
include 'name', 'disk_format', 'container_format',
'status', 'size_min', 'size_max' and 'changes-since.'
Any extra fields are treated as image metadata properties"""
    client = get_client(options)
    filters = get_image_filters_from_args(args)
    limit = options.limit
    marker = options.marker
    sort_key = options.sort_key
    sort_dir = options.sort_dir

    return _images_index(client,
                         filters,
                         limit,
                         marker=marker,
                         sort_key=sort_key,
                         sort_dir=sort_dir,
                         print_header=True)


def _images_details(client, filters, limit, print_header=False, **kwargs):
    """Driver function for images_details"""
    parameters = {
        "filters": filters,
        "limit": limit,
    }

    optional_kwargs = ['marker', 'sort_key', 'sort_dir']
    for kwarg in optional_kwargs:
        if kwarg in kwargs:
            parameters[kwarg] = kwargs[kwarg]

    images = client.get_images_detailed(**parameters)

    if len(images) == 0:
        return SUCCESS

    if print_header:
        print "=" * 80

    for image in images:
        print_image_formatted(client, image)
        print "=" * 80

    if not (options.force or len(images) != limit or
            user_confirm("Fetch next page?", True)):
        return SUCCESS

    parameters["marker"] = images[-1]['id']
    return _images_details(client, **parameters)


@catch_error('show details')
def images_details(options, args):
    """
%(prog)s details [options]

Returns detailed information for all public images
a Glance server knows about. Provided fields are
handled as query filters. Supported filters
include 'name', 'disk_format', 'container_format',
'status', 'size_min', 'size_max' and 'changes-since.'
Any extra fields are treated as image metadata properties"""
    client = get_client(options)
    filters = get_image_filters_from_args(args)
    limit = options.limit
    marker = options.marker
    sort_key = options.sort_key
    sort_dir = options.sort_dir

    return _images_details(client,
                           filters,
                           limit,
                           marker=marker,
                           sort_key=sort_key,
                           sort_dir=sort_dir,
                           print_header=True)


def images_clear(options, args):
    """
%(prog)s clear [options]

Deletes all images from a Glance server"""
    if not (options.force or
            user_confirm("Delete all images?", default=False)):
        print 'Not deleting any images'
        return FAILURE

    c = get_client(options)
    images = c.get_images()
    for image in images:
        if options.verbose:
            print 'Deleting image %s "%s" ...' % (image['id'], image['name']),
        try:
            c.delete_image(image['id'])
            if options.verbose:
                print 'done'
        except Exception as e:
            print 'Failed to delete image %s' % image['id']
            print e
            return FAILURE
    return SUCCESS


def get_client(options):
    """
    Returns a new client object to a Glance server
    specified by the --host and --port options
    supplied to the CLI
    """
    return glance_client.get_client(host=options.host,
                                    port=options.port,
                                    timeout=options.timeout,
                                    use_ssl=options.use_ssl,
                                    username=options.os_username,
                                    password=options.os_password,
                                    tenant=options.os_tenant_name,
                                    auth_url=options.os_auth_url,
                                    auth_strategy=options.os_auth_strategy,
                                    auth_token=options.os_auth_token,
                                    region=options.os_region_name,
                                    is_silent_upload=options.is_silent_upload,
                                    insecure=options.insecure)


def create_options(parser):
    """
    Sets up the CLI and config-file options that may be
    parsed and program commands.

    :param parser: The option parser
    """
    parser.add_option('--silent-upload', default=False, action="store_true",
                      dest="is_silent_upload",
                      help="disable progress bar animation and information "
                      "during upload")
    parser.add_option('-v', '--verbose', default=False, action="store_true",
                      help="Print more verbose output")
    parser.add_option('-d', '--debug', default=False, action="store_true",
                      help="Print debugging output")
    parser.add_option('-H', '--host', metavar="ADDRESS", default="0.0.0.0",
                      help="Address of Glance API host. "
                           "Default: %default")
    parser.add_option('-p', '--port', dest="port", metavar="PORT",
                      type=int, default=DEFAULT_PORT,
                      help="Port the Glance API host listens on. "
                           "Default: %default")
    parser.add_option('-t', '--timeout', dest="timeout", metavar="TIMEOUT",
                      type=int, default=None,
                      help="Connection timeout.")
    parser.add_option('--ssl', dest='use_ssl',
                      default=False, action="store_true",
                      help="Use SSL when talking to Glance API host")
    parser.add_option('-U', '--url', metavar="URL", default=None,
                      help="URL of Glance service. This option can be used "
                           "to specify the hostname, port and protocol "
                           "(http/https) of the glance server, for example "
                           "-U https://localhost:" + str(DEFAULT_PORT) +
                           "/v1 Default: None. If given, this option will "
                           "override settings for --host, --port, and --ssl.")
    parser.add_option('-k', '--insecure', dest="insecure",
                      default=False, action="store_true",
                      help="Explicitly allow glance to perform \"insecure\" "
                      "SSL (https) requests. The server's certificate will "
                      "not be verified against any certificate authorities. "
                      "This option should be used with caution.")
    parser.add_option('-A', '--os_auth_token', '--auth_token',
                      dest="os_auth_token", metavar="TOKEN", default=None,
                      help="Authentication token to use to identify the "
                           "client to the glance server.  --auth_token "
                           "is deprecated and will be removed")
    parser.add_option('-I', '--os_username', dest="os_username",
                      metavar="USER", default=None,
                      help="User name used to acquire an authentication token")
    parser.add_option('-K', '--os_password', dest="os_password",
                      metavar="PASSWORD", default=None,
                      help="Password used to acquire an authentication token")
    parser.add_option('-R', '--os_region_name', dest="os_region_name",
                      metavar="REGION", default=None,
                      help="Region name. When using keystone authentication "
                      "version 2.0 or later this identifies the region "
                      "name to use when selecting the service endpoint. A "
                      "region name must be provided if more than one "
                      "region endpoint is available")
    parser.add_option('-T', '--os_tenant_name', dest="os_tenant_name",
                      metavar="TENANT", default=None,
                      help="Tenant name")
    parser.add_option('-N', '--os_auth_url', dest="os_auth_url",
                      metavar="AUTH_URL", default=None,
                      help="Authentication URL")
    parser.add_option('-S', '--os_auth_strategy', dest="os_auth_strategy",
                      metavar="STRATEGY", default=None,
                      help="Authentication strategy (keystone or noauth)")
    parser.add_option('--limit', dest="limit", metavar="LIMIT", default=10,
                      type="int", help="Page size to use while "
                                       "requesting image metadata")
    parser.add_option('--marker', dest="marker", metavar="MARKER",
                      default=None, help="Image index after which to "
                                         "begin pagination")
    parser.add_option('--sort_key', dest="sort_key", metavar="KEY",
                      help="Sort results by this image attribute.")
    parser.add_option('--sort_dir', dest="sort_dir", metavar="[desc|asc]",
                      help="Sort results in this direction.")
    parser.add_option('-f', '--force', dest="force",
                      default=False, action="store_true",
                      help="Prevent select actions from requesting "
                           "user confirmation")
    parser.add_option('--dry-run', default=False, action="store_true",
                      help="Don't actually execute the command, just print "
                           "output showing what WOULD happen.")
    parser.add_option('--can-share', default=False, action="store_true",
                      help="Allow member to further share image.")


def parse_options(parser, cli_args):
    """
    Returns the parsed CLI options, command to run and its arguments, merged
    with any same-named options found in a configuration file

    :param parser: The option parser
    """
    if not cli_args:
        cli_args.append('-h')  # Show options in usage output...

    (options, args) = parser.parse_args(cli_args)
    if options.url is not None:
        u = urlparse(options.url)
        options.port = u.port
        options.host = u.hostname
        options.use_ssl = (u.scheme == 'https')

    # HACK(sirp): Make the parser available to the print_help method
    # print_help is a command, so it only accepts (options, args); we could
    # one-off have it take (parser, options, args), however, for now, I think
    # this little hack will suffice
    options.__parser = parser

    if not args:
        parser.print_usage()
        sys.exit(0)

    command_name = args.pop(0)
    command = lookup_command(parser, command_name)

    return (options, command, args)


def print_help(options, args):
    """
    Print help specific to a command
    """
    if len(args) != 1:
        sys.exit("Please specify a command")

    parser = options.__parser
    command_name = args.pop()
    command = lookup_command(parser, command_name)

    print command.__doc__ % {'prog': os.path.basename(sys.argv[0])}


def lookup_command(parser, command_name):
    BASE_COMMANDS = {'help': print_help}

    IMAGE_COMMANDS = {
        'add': image_add,
        'update': image_update,
        'delete': image_delete,
        'index': images_index,
        'details': images_details,
        'show': image_show,
        'clear': images_clear}

    commands = {}
    for command_set in (BASE_COMMANDS, IMAGE_COMMANDS):
        commands.update(command_set)

    try:
        command = commands[command_name]
    except KeyError:
        parser.print_usage()
        sys.exit("Unknown command: %s" % command_name)

    return command


def user_confirm(prompt, default=False):
    """
    Yes/No question dialog with user.

    :param prompt: question/statement to present to user (string)
    :param default: boolean value to return if empty string
                    is received as response to prompt

    """
    if default:
        prompt_default = "[Y/n]"
    else:
        prompt_default = "[y/N]"

    # for bug 884116, don't issue the prompt if stdin isn't a tty
    if not (hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()):
        return default

    answer = raw_input("%s %s " % (prompt, prompt_default))

    if answer == "":
        return default
    else:
        return answer.lower() in ("yes", "y")


if __name__ == '__main__':
    usage = """
%prog <command> [options] [args]

WARNING! This tool is deprecated in favor of python-glanceclient (see
http://github.com/openstack/python-glanceclient).

Commands:

    help <command>  Output help for one of the commands below

    add             Adds a new image to Glance

    update          Updates an image's metadata in Glance

    delete          Deletes an image from Glance

    index           Return brief information about images in Glance

    details         Return detailed information about images in
                    Glance

    show            Show detailed information about an image in
                    Glance

    clear           Removes all images and metadata from Glance
"""

    #print >> sys.stderr, ("WARNING! This tool is deprecated in favor of "
                          #"python-glanceclient (see "
                          #"http://github.com/openstack/python-glanceclient).")

    oparser = optparse.OptionParser(version='%%prog %s'
                                    % version.version_string(),
                                    usage=usage.strip())
    create_options(oparser)
    (options, command, args) = parse_options(oparser, sys.argv[1:])

    try:
        start_time = time.time()
        result = command(options, args)
        end_time = time.time()
        if options.verbose:
            print "Completed in %-0.4f sec." % (end_time - start_time)
        sys.exit(result)
    except (RuntimeError,
            NotImplementedError,
            exception.ClientConfigurationError) as e:
        oparser.print_usage()
        print >> sys.stderr, "ERROR: ", e
        sys.exit(1)
