#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:guestfs.py
# Date:Mon Oct 21 10:42:30 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
from eventlet import tpool
from common import log as logging
from virt.disk.vfs import api as vfs
LOG = logging.getLogger('agent')
guestfs = None


class VFSGuestFS(vfs.VFS):

    """
    This class implements a VFS module that uses the libguestfs APIs
    to access the disk image. The disk image is never mapped into
    the host filesystem, thus avoiding any potential for symlink
    attacks from the guest filesystem.
    """
    def __init__(self, imgfile, imgfmt='raw', partition=None):
        super(VFSGuestFS, self).__init__(imgfile, imgfmt, partition)

        global guestfs
        if guestfs is None:
            guestfs = __import__('guestfs')

        self.handle = None

    def setup_os(self):
        if self.partition == -1:
            self.setup_os_inspect()
        else:
            self.setup_os_static()

    def setup_os_static(self):
        LOG.debug("Mount guest OS image %(imgfile)s partition %(part)s" %
                  {'imgfile': self.imgfile, 'part': str(self.partition)})

        if self.partition:
            self.handle.mount_options("", "/dev/sda%d" % self.partition, "/")
        else:
            self.handle.mount_options("", "/dev/sda", "/")

    def setup_os_inspect(self):
        LOG.debug("Inspecting guest OS image %s" % self.imgfile)
        roots = self.handle.inspect_os()

        if len(roots) == 0:
            raise Exception("No operating system found in %s" % self.imgfile)

        if len(roots) != 1:
            LOG.debug("Multi-boot OS %(roots)s" % {'roots': str(roots)})
            raise Exception(
                "Multi-boot operating system found in %s" %
                self.imgfile)

        self.setup_os_root(roots[0])

    def setup_os_root(self, root):
        LOG.debug("Inspecting guest OS root filesystem %s" % root)
        mounts = self.handle.inspect_get_mountpoints(root)

        if len(mounts) == 0:
            raise Exception(
                "No mount points found in %(root)s of %(imgfile)s" %
                {'root': root, 'imgfile': self.imgfile})

        mounts.sort(key=lambda mount: mount[1])
        for mount in mounts:
            LOG.debug("Mounting %(dev)s at %(dir)s" %
                      {'dev': mount[1], 'dir': mount[0]})
            self.handle.mount_options("", mount[1], mount[0])

    def setup(self):
        LOG.debug("Setting up appliance for %(imgfile)s %(imgfmt)s" %
                  {'imgfile': self.imgfile, 'imgfmt': self.imgfmt})
        self.handle = tpool.Proxy(guestfs.GuestFS())

        try:
            self.handle.add_drive_opts(self.imgfile, format=self.imgfmt)
            if self.handle.get_attach_method() == 'libvirt':
                libvirt_url = 'libvirt:' + 'qemu:///system'
                self.handle.set_attach_method(libvirt_url)
            self.handle.launch()

            self.setup_os()

            self.handle.aug_init("/", 0)
        except RuntimeError as e:
            # dereference object and implicitly close()
            self.handle = None
            raise Exception(
                "Error mounting %(imgfile)s with libguestfs (%(e)s)" %
                {'imgfile': self.imgfile, 'e': e})
        except Exception:
            self.handle = None
            raise

    def teardown(self):
        LOG.debug("Tearing down appliance")

        try:
            try:
                self.handle.aug_close()
            except RuntimeError as e:
                LOG.warn("Failed to close augeas %s" % e)

            try:
                self.handle.shutdown()
            except AttributeError:
                # Older libguestfs versions haven't an explicit shutdown
                pass
            except RuntimeError as e:
                LOG.warn("Failed to shutdown appliance %s" % e)

            try:
                self.handle.close()
            except AttributeError:
                # Older libguestfs versions haven't an explicit close
                pass
            except RuntimeError as e:
                LOG.warn("Failed to close guest handle %s" % e)
        finally:
            # dereference object and implicitly close()
            self.handle = None

    @staticmethod
    def _canonicalize_path(path):
        if path[0] != '/':
            return '/' + path
        return path

    def make_path(self, path):
        LOG.debug("Make directory path=%s" % path)
        path = self._canonicalize_path(path)
        self.handle.mkdir_p(path)

    def append_file(self, path, content):
        LOG.debug("Append file path=%s" % path)
        path = self._canonicalize_path(path)
        self.handle.write_append(path, content)

    def replace_file(self, path, content):
        LOG.debug("Replace file path=%s" % path)
        path = self._canonicalize_path(path)
        self.handle.write(path, content)

    def read_file(self, path):
        LOG.debug("Read file path=%s" % path)
        path = self._canonicalize_path(path)
        return self.handle.read_file(path)

    def has_file(self, path):
        LOG.debug("Has file path=%s" % path)
        path = self._canonicalize_path(path)
        try:
            self.handle.stat(path)
            return True
        except RuntimeError:
            return False

    def set_permissions(self, path, mode):
        LOG.debug("Set permissions path=%(path)s mode=%(mode)s" %
                  {'path': path, 'mode': mode})
        path = self._canonicalize_path(path)
        self.handle.chmod(mode, path)

    def set_ownership(self, path, user, group):
        LOG.debug("Set ownership path=%(path)s user=%(user)s group=%(group)s" %
                  {'path': path, 'user': user, 'group': group})
        path = self._canonicalize_path(path)
        uid = -1
        gid = -1

        if user is not None:
            uid = int(self.handle.aug_get(
                "/files/etc/passwd/" + user + "/uid"))
        if group is not None:
            gid = int(self.handle.aug_get(
                "/files/etc/group/" + group + "/gid"))

        LOG.debug("chown uid=%(uid)d gid=%(gid)s" %
                  {'uid': uid, 'gid': gid})
        self.handle.chown(uid, gid, path)
