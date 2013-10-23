#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:api.py
# Date:Mon Oct 21 10:14:39 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
"""
Utility methods to resize, repartition, and modify disk images.

Includes injection of SSH PGP keys into authorized_keys file.

"""
import os
import random
import tempfile

if os.name != 'nt':
    import crypt

from common import log as logging
from virt import utils
from virt.disk.mount import api as mount
from virt.disk.vfs import api as vfs
from virt import images
LOG = logging.getLogger('agent')


def mkfs(os_type, fs_label, target):
    utils.execute('mkfs.ext3', '-L', fs_label, target, run_as_root=True)


def resize2fs(image, check_exit_code=False, run_as_root=False):
    utils.execute('e2fsck', '-fp', image,
                  check_exit_code=check_exit_code,
                  run_as_root=run_as_root)
    utils.execute('resize2fs', image,
                  check_exit_code=check_exit_code,
                  run_as_root=run_as_root)


def get_disk_size(path):
    """Get the (virtual) size of a disk image

    :param path: Path to the disk image
    :returns: Size (in bytes) of the given disk image as it would be seen
              by a virtual machine.
    """
    return images.qemu_img_info(path).virtual_size


def extend(image, size):
    """Increase image to size."""
    virt_size = get_disk_size(image)
    if virt_size >= size:
        return
    utils.execute('qemu-img', 'resize', image, size)
    resize2fs(image)


def can_resize_fs(image, size, use_cow=False):
    """Check whether we can resize contained file system."""

    LOG.debug("Checking if we can resize image %(image)s. size=%(size)s, CoW=%(use_cow)s" %
              {'image': image, 'size': size, 'use_cow': use_cow})

    # Check that we're increasing the size
    virt_size = get_disk_size(image)
    if virt_size >= size:
        LOG.debug("Cannot resize filesystem %s to a smaller size." %
                  image)
        return False

    # Check the image is unpartitioned
    if use_cow:
        try:
            fs = vfs.VFS.instance_for_image(image, 'qcow2', None)
            fs.setup()
            fs.teardown()
        except Exception as e:
            LOG.debug("Unable to mount image %(image)s with error %(error)s. Cannot resize." %
                      {'image': image,
                       'error': e})
            return False
    else:
        # For raw, we can directly inspect the file system
        try:
            utils.execute('e2label', image)
        except Exception as e:
            LOG.debug("Unable to determine label for image %(image)s with error %(errror)s. Cannot resize." %
                      {'image': image,
                       'error': e})
            return False

    return True


class _DiskImage(object):

    """Provide operations on a disk image file."""

    tmp_prefix = 'ccf-disk-mount-tmp'

    def __init__(self, image, partition=None, use_cow=True, mount_dir=None):
        # These passed to each mounter
        self.image = image
        self.partition = partition
        self.mount_dir = mount_dir
        self.use_cow = use_cow

        # Internal
        self._mkdir = False
        self._mounter = None
        self._errors = []

        if mount_dir:
            device = self._device_for_path(mount_dir)
            if device:
                self._reset(device)

    @staticmethod
    def _device_for_path(path):
        device = None
        path = os.path.realpath(path)
        with open("/proc/mounts", 'r') as ifp:
            for line in ifp:
                fields = line.split()
                if fields[1] == path:
                    device = fields[0]
                    break
        return device

    def _reset(self, device):
        """Reset internal state for a previously mounted directory."""
        self._mounter = mount.Mount.instance_for_device(self.image,
                                                        self.mount_dir,
                                                        self.partition,
                                                        device)

        mount_name = os.path.basename(self.mount_dir or '')
        self._mkdir = mount_name.startswith(self.tmp_prefix)

    @property
    def errors(self):
        """Return the collated errors from all operations."""
        return '\n--\n'.join([''] + self._errors)

    def mount(self):
        """Mount a disk image, using the object attributes.

        The first supported means provided by the mount classes is used.

        True, or False is returned and the 'errors' attribute
        contains any diagnostics.
        """
        if self._mounter:
            raise Exception("image already mounted")

        if not self.mount_dir:
            self.mount_dir = tempfile.mkdtemp(prefix=self.tmp_prefix)
            self._mkdir = True

        imgfmt = "raw"
        if self.use_cow:
            imgfmt = "qcow2"

        mounter = mount.Mount.instance_for_format(self.image,
                                                  self.mount_dir,
                                                  self.partition,
                                                  imgfmt)
        if mounter.do_mount():
            self._mounter = mounter
        else:
            LOG.debug(mounter.error)
            self._errors.append(mounter.error)

        return bool(self._mounter)

    def umount(self):
        """Umount a mount point from the filesystem."""
        if self._mounter:
            self._mounter.do_umount()
            self._mounter = None

    def teardown(self):
        """Remove a disk image from the file system."""
        try:
            if self._mounter:
                self._mounter.do_teardown()
                self._mounter = None
        finally:
            if self._mkdir:
                os.rmdir(self.mount_dir)


# Public module functions

def inject_data(image, key=None, net=None, metadata=None, admin_password=None,
                files=None, partition=None, use_cow=True, mandatory=()):
    """Inject the specified items into a disk image.

    If an item name is not specified in the MANDATORY iterable, then a warning
    is logged on failure to inject that item, rather than raising an exception.

    it will mount the image as a fully partitioned disk and attempt to inject
    into the specified partition number.

    If PARTITION is not specified the image is mounted as a single partition.

    Returns True if all requested operations completed without issue.
    Raises an exception if a mandatory item can't be injected.
    """
    LOG.debug("Inject data image=%(image)s key=%(key)s net=%(net)s metadata=%(metadata)s admin_password=<SANITIZED> files=%(files)s partition=%(partition)s use_cow=%(use_cow)s" %
              {'image': image, 'key': key, 'net': net, 'metadata': metadata,
               'files': files, 'partition': partition, 'use_cow': use_cow})
    fmt = "raw"
    if use_cow:
        fmt = "qcow2"
    try:
        fs = vfs.VFS.instance_for_image(image, fmt, partition)
        fs.setup()
    except Exception as e:
        # If a mandatory item is passed to this function,
        # then reraise the exception to indicate the error.
        for inject in mandatory:
            inject_val = locals()[inject]
            if inject_val:
                raise
        LOG.warn("Ignoring error injecting data into image (%(e)s)" %
                 {'e': e})
        return False

    try:
        return inject_data_into_fs(fs, key, net, metadata,
                                   admin_password, files, mandatory)
    finally:
        fs.teardown()


def inject_data_into_fs(fs, key, net, metadata, admin_password, files,
                        mandatory=()):
    """Injects data into a filesystem already mounted by the caller.
    Virt connections can call this directly if they mount their fs
    in a different way to inject_data.

    If an item name is not specified in the MANDATORY iterable, then a warning
    is logged on failure to inject that item, rather than raising an exception.

    Returns True if all requested operations completed without issue.
    Raises an exception if a mandatory item can't be injected.
    """
    status = True
    for inject in ('key', 'net', 'metadata', 'admin_password', 'files'):
        inject_val = locals()[inject]
        inject_func = globals()['_inject_%s_into_fs' % inject]
        if inject_val:
            try:
                inject_func(inject_val, fs)
            except Exception as e:
                if inject in mandatory:
                    raise
                LOG.warn("Ignoring error injecting %(inject)s into image (%(e)s)" % {
                         'e': e, 'inject': inject})
                status = False
    return status


def _inject_files_into_fs(files, fs):
    for (path, contents) in files:
        _inject_file_into_fs(fs, path, contents)


def _inject_file_into_fs(fs, path, contents, append=False):
    LOG.debug("Inject file fs=%(fs)s path=%(path)s append=%(append)s" %
              {'fs': fs, 'path': path, 'append': append})
    if append:
        fs.append_file(path, contents)
    else:
        fs.replace_file(path, contents)


def _inject_metadata_into_fs(metadata, fs):
    LOG.debug("Inject metadata fs=%(fs)s metadata=%(metadata)s" %
              {'fs': fs, 'metadata': metadata})
#def _inject_metadata_into_fs(metadata, fs):
    #LOG.debug("Inject metadata fs=%(fs)s metadata=%(metadata)s" %
              #{'fs': fs, 'metadata': metadata})
    #metadata = dict([(m['key'], m['value']) for m in metadata])
    #_inject_file_into_fs(fs, 'meta.js', jsonutils.dumps(metadata))


def _setup_selinux_for_keys(fs, sshdir):
    """Get selinux guests to ensure correct context on injected keys."""

    if not fs.has_file(os.path.join("etc", "selinux")):
        return

    rclocal = os.path.join('etc', 'rc.local')
    rc_d = os.path.join('etc', 'rc.d')

    if not fs.has_file(rclocal) and fs.has_file(rc_d):
        rclocal = os.path.join(rc_d, 'rc.local')

    # Note some systems end rc.local with "exit 0"
    # and so to append there you'd need something like:
    #  utils.execute('sed', '-i', '${/^exit 0$/d}' rclocal, run_as_root=True)
    restorecon = [
        '\n',
        '# Added by Nova to ensure injected ssh keys have the right context\n',
        'restorecon -RF %s 2>/dev/null || :\n' % sshdir,
    ]

    if not fs.has_file(rclocal):
        restorecon.insert(0, '#!/bin/sh')

    _inject_file_into_fs(fs, rclocal, ''.join(restorecon), append=True)
    fs.set_permissions(rclocal, 0o700)


def _inject_key_into_fs(key, fs):
    """Add the given public ssh key to root's authorized_keys.

    key is an ssh key string.
    fs is the path to the base of the filesystem into which to inject the key.
    """

    LOG.debug("Inject key fs=%(fs)s key=%(key)s" % {'fs': fs, 'key': key})
    sshdir = os.path.join('root', '.ssh')
    fs.make_path(sshdir)
    fs.set_ownership(sshdir, "root", "root")
    fs.set_permissions(sshdir, 0o700)

    keyfile = os.path.join(sshdir, 'authorized_keys')

    key_data = ''.join([
        '\n',
        '# The following ssh key was injected by Nova',
        '\n',
        key.strip(),
        '\n',
    ])

    _inject_file_into_fs(fs, keyfile, key_data, append=True)
    fs.set_permissions(keyfile, 0o600)

    _setup_selinux_for_keys(fs, sshdir)


def _inject_net_into_fs(net, fs):
    """Inject /etc/network/interfaces into the filesystem rooted at fs.

    net is the contents of /etc/network/interfaces.
    """

    LOG.debug("Inject key fs=%(fs)s net=%(net)s" % {'fs': fs, 'net': net})
    netdir = os.path.join('etc', 'network')
    fs.make_path(netdir)
    fs.set_ownership(netdir, "root", "root")
    fs.set_permissions(netdir, 0o744)

    netfile = os.path.join('etc', 'network', 'interfaces')
    _inject_file_into_fs(fs, netfile, net)


def _inject_admin_password_into_fs(admin_passwd, fs):
    """Set the root password to admin_passwd

    admin_password is a root password
    fs is the path to the base of the filesystem into which to inject
    the key.

    This method modifies the instance filesystem directly,
    and does not require a guest agent running in the instance.

    """
    # The approach used here is to copy the password and shadow
    # files from the instance filesystem to local files, make any
    # necessary changes, and then copy them back.

    LOG.debug("Inject admin password fs=%(fs)s admin_passwd=<SANITIZED>" %
              {'fs': fs})
    admin_user = 'root'

    fd, tmp_passwd = tempfile.mkstemp()
    os.close(fd)
    fd, tmp_shadow = tempfile.mkstemp()
    os.close(fd)

    passwd_path = os.path.join('etc', 'passwd')
    shadow_path = os.path.join('etc', 'shadow')

    passwd_data = fs.read_file(passwd_path)
    shadow_data = fs.read_file(shadow_path)

    new_shadow_data = _set_passwd(admin_user, admin_passwd,
                                  passwd_data, shadow_data)

    fs.replace_file(shadow_path, new_shadow_data)


def _generate_salt():
    salt_set = ('abcdefghijklmnopqrstuvwxyz'
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                '0123456789./')
    salt = 16 * ' '
    return ''.join([random.choice(salt_set) for c in salt])


def _set_passwd(username, admin_passwd, passwd_data, shadow_data):
    """set the password for username to admin_passwd

    The passwd_file is not modified.  The shadow_file is updated.
    if the username is not found in both files, an exception is raised.

    :param username: the username
    :param encrypted_passwd: the  encrypted password
    :param passwd_file: path to the passwd file
    :param shadow_file: path to the shadow password file
    :returns: nothing
    :raises: exception.NovaException(), IOError()

    """
    if os.name == 'nt':
        raise Exception("Not implemented on Windows")

    # encryption algo - id pairs for crypt()
    algos = {'SHA-512': '$6$', 'SHA-256': '$5$', 'MD5': '$1$', 'DES': ''}

    salt = _generate_salt()

    # crypt() depends on the underlying libc, and may not support all
    # forms of hash. We try md5 first. If we get only 13 characters back,
    # then the underlying crypt() didn't understand the '$n$salt' magic,
    # so we fall back to DES.
    # md5 is the default because it's widely supported. Although the
    # local crypt() might support stronger SHA, the target instance
    # might not.
    encrypted_passwd = crypt.crypt(admin_passwd, algos['MD5'] + salt)
    if len(encrypted_passwd) == 13:
        encrypted_passwd = crypt.crypt(admin_passwd, algos['DES'] + salt)

    p_file = passwd_data.split("\n")
    s_file = shadow_data.split("\n")

     # username MUST exist in passwd file or it's an error
    found = False
    for entry in p_file:
        split_entry = entry.split(':')
        if split_entry[0] == username:
            found = True
            break
    if not found:
        msg = "User %(username)s not found in password file."
        raise Exception(msg % username)

    # update password in the shadow file.It's an error if the
    # the user doesn't exist.
    new_shadow = list()
    found = False
    for entry in s_file:
        split_entry = entry.split(':')
        if split_entry[0] == username:
            split_entry[1] = encrypted_passwd
            found = True
        new_entry = ':'.join(split_entry)
        new_shadow.append(new_entry)

    if not found:
        msg = "User %(username)s not found in shadow file."
        raise Exception(msg % username)

    return "\n".join(new_shadow)