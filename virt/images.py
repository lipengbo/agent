#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:images.py
# Date:Mon Oct 21 02:24:03 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
"""
Handling of VM disk images.
"""
import os
import re
from common import log as logging
from virt import utils
import urllib2
import threading
LOG = logging.getLogger('agent')
MUTEX = threading.RLock()


BYTE_MULTIPLIERS = {
    '': 1,
    't': 1024 ** 4,
    'g': 1024 ** 3,
    'm': 1024 ** 2,
    'k': 1024,
}
BYTE_REGEX = re.compile(r'(^-?\d+\.*\d*)(\D*)')


def to_bytes(text, default=0):
    """Converts a string into an integer of bytes.

    Looks at the last characters of the text to determine
    what conversion is needed to turn the input text into a byte number.
    Supports "B, K(B), M(B), G(B), and T(B)". (case insensitive)

    :param text: String input for bytes size conversion.
    :param default: Default return value when text is blank.

    """
    match = BYTE_REGEX.search(text)
    if match:
        magnitude = float(match.group(1))
        mult_key_org = match.group(2)
        if not mult_key_org:
            return magnitude
    elif text:
        msg = 'Invalid string format: %s' % text
        raise TypeError(msg)
    else:
        return default
    mult_key = mult_key_org.lower().replace('b', '', 1)
    multiplier = BYTE_MULTIPLIERS.get(mult_key)
    if multiplier is None:
        msg = 'Unknown byte multiplier: %s' % mult_key_org
        raise TypeError(msg)
    return magnitude * multiplier


class QemuImgInfo(object):
    BACKING_FILE_RE = re.compile((r"^(.*?)\s*\(actual\s+path\s*:"
                                  r"\s+(.*?)\)\s*$"), re.I)
    TOP_LEVEL_RE = re.compile(r"^([\w\d\s\_\-]+):(.*)$")
    SIZE_RE = re.compile(r"\(\s*(\d+)\s+bytes\s*\)", re.I)

    def __init__(self, cmd_output=None):
        details = self._parse(cmd_output or '')
        self.image = details.get('image')
        self.backing_file = details.get('backing_file')
        self.file_format = details.get('file_format')
        self.virtual_size = details.get('virtual_size')
        self.cluster_size = details.get('cluster_size')
        self.disk_size = details.get('disk_size')
        self.snapshots = details.get('snapshot_list', [])
        self.encryption = details.get('encryption')

    def __str__(self):
        lines = [
            'image: %s' % self.image,
            'file_format: %s' % self.file_format,
            'virtual_size: %s' % self.virtual_size,
            'disk_size: %s' % self.disk_size,
            'cluster_size: %s' % self.cluster_size,
            'backing_file: %s' % self.backing_file,
        ]
        if self.snapshots:
            lines.append("snapshots: %s" % self.snapshots)
        return "\n".join(lines)

    def _canonicalize(self, field):
        # Standardize on underscores/lc/no dash and no spaces
        # since qemu seems to have mixed outputs here... and
        # this format allows for better integration with python
        # - ie for usage in kwargs and such...
        field = field.lower().strip()
        for c in (" ", "-"):
            field = field.replace(c, '_')
        return field

    def _extract_bytes(self, details):
        # Replace it with the byte amount
        real_size = self.SIZE_RE.search(details)
        if real_size:
            details = real_size.group(1)
        try:
            details = to_bytes(details)
        except TypeError:
            pass
        return details

    def _extract_details(self, root_cmd, root_details, lines_after):
        real_details = root_details
        if root_cmd == 'backing_file':
            # Replace it with the real backing file
            backing_match = self.BACKING_FILE_RE.match(root_details)
            if backing_match:
                real_details = backing_match.group(2).strip()
        elif root_cmd in ['virtual_size', 'cluster_size', 'disk_size']:
            # Replace it with the byte amount (if we can convert it)
            real_details = self._extract_bytes(root_details)
        elif root_cmd == 'file_format':
            real_details = real_details.strip().lower()
        elif root_cmd == 'snapshot_list':
            # Next line should be a header, starting with 'ID'
            if not lines_after or not lines_after[0].startswith("ID"):
                msg = "Snapshot list encountered but no header found!"
                raise ValueError(msg)
            del lines_after[0]
            real_details = []
            # This is the sprintf pattern we will try to match
            # "%-10s%-20s%7s%20s%15s"
            # ID TAG VM SIZE DATE VM CLOCK (current header)
            while lines_after:
                line = lines_after[0]
                line_pieces = line.split()
                if len(line_pieces) != 6:
                    break
                # Check against this pattern in the final position
                # "%02d:%02d:%02d.%03d"
                date_pieces = line_pieces[5].split(":")
                if len(date_pieces) != 3:
                    break
                real_details.append({
                    'id': line_pieces[0],
                    'tag': line_pieces[1],
                    'vm_size': line_pieces[2],
                    'date': line_pieces[3],
                    'vm_clock': line_pieces[4] + " " + line_pieces[5],
                })
                del lines_after[0]
        return real_details

    def _parse(self, cmd_output):
        contents = {}
        lines = [x for x in cmd_output.splitlines() if x.strip()]
        while lines:
            line = lines.pop(0)
            top_level = self.TOP_LEVEL_RE.match(line)
            if top_level:
                root = self._canonicalize(top_level.group(1))
                if not root:
                    continue
                root_details = top_level.group(2).strip()
                details = self._extract_details(root, root_details, lines)
                contents[root] = details
        return contents


def qemu_img_info(path):
    """Return an object containing the parsed output from qemu-img info."""
    if not os.path.exists(path):
        return QemuImgInfo()

    out, err = utils.execute('env', 'LC_ALL=C', 'LANG=C',
                             'qemu-img', 'info', path)
    return QemuImgInfo(out)


def convert_image(source, dest, out_format, run_as_root=False):
    """Convert image to other format."""
    cmd = ('qemu-img', 'convert', '-O', out_format, source, dest)
    utils.execute(*cmd, run_as_root=run_as_root)


def fetch_with_urllib2(url, target):
    request = urllib2.urlopen(url)
    content_buffer = 16 << 10
    with open(target, 'wb') as fp:
        for content in iter(lambda: request.read(content_buffer), ''):
            fp.write(content)


def fetch_with_wget(url, target):
    cmd = ('wget', '-c', '--timeout=3', '-t', '5', url, '-O', target)
    utils.execute(*cmd)


def fetch(url, target, method=fetch_with_wget):
    MUTEX.acquire()
    try:
        LOG.debug('Downloading Image %s' % target)
        method(url, target)
    except:
        raise
    finally:
        MUTEX.release()


def get_disk_backing_file(path):
    """Get the backing file of a disk image

    :param path: Path to the disk image
    :returns: a path to the image's backing store
    """
    out, err = utils.execute('qemu-img', 'info', path)
    backing_file = None

    for line in out.split('\n'):
        if line.startswith('backing file: '):
            if 'actual path: ' in line:
                backing_file = line.split('actual path: ')[1][:-1]
            else:
                backing_file = line.split('backing file: ')[1]
            break
    if backing_file:
        backing_file = os.path.basename(backing_file)

    return backing_file


def create_cow_image(backing_file, path, size_gb):
    """Create COW image

    Creates a COW image with the given backing file

    :param backing_file: Existing image on which to base the COW image
    :param path: Desired location of the COW image
    """
    #return utils.execute('qemu-img', 'create', '-f', 'qcow2', '-o', 'backing_file=%s' % backing_file, path)
    return utils.execute('qemu-img', 'convert', '-f', 'qcow2', '-O', 'raw', backing_file, path)
