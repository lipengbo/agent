#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:utils.py
# Date:Mon May 27 17:09:37 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com

"""
System-level utilities and helper functions.
"""

import os
import signal
import re
from eventlet.green import subprocess
from eventlet import greenthread
import random
import log as logging
LOG = logging.getLogger("agent.libs.excutils")


def abspath(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


IPTABLES_BAK_FILE = abspath('../etc/iptables.bak')
IP_BAK_FILE = abspath('../etc/ip.bak')


class InvalidArgumentError(Exception):

    def __init__(self, message=None):
        super(InvalidArgumentError, self).__init__(message)


class UnknownArgumentError(Exception):

    def __init__(self, message=None):
        super(UnknownArgumentError, self).__init__(message)


class ProcessExecutionError(Exception):

    def __init__(self, stdout=None, stderr=None, exit_code=None, cmd=None,
                 description=None):
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.cmd = cmd
        self.description = description

        if description is None:
            description = "Unexpected error while running command."
        if exit_code is None:
            exit_code = '-'
        message = ("%s\nCommand: %s\nExit code: %s\nStdout: %r\nStderr: %r"
                   % (description, cmd, exit_code, stdout, stderr))
        super(ProcessExecutionError, self).__init__(message)


class NoRootWrapSpecified(Exception):

    def __init__(self, message=None):
        super(NoRootWrapSpecified, self).__init__(message)


def _subprocess_setup():
    # Python installs a SIGPIPE handler by default. This is usually not what
    # non-Python subprocesses expect.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def execute(cmd, process_input=None, addl_env=None, check_exit_code=True):
    result, errors = _execute(cmd, process_input, addl_env, check_exit_code)
    if not errors:
        if ('ip addr add' in cmd) or ('ip route add' in cmd):
            with open(IP_BAK_FILE, 'a') as ipFile:
                ipFile.write(cmd + "\n")
        if ('ip addr del' in cmd) or ('ip route del' in cmd):
            temp_cmd = re.sub("del", 'add', cmd) + "\n"
            with open(IP_BAK_FILE, 'r') as ipFile:
                content = ipFile.readlines()
            if temp_cmd in content:
                content.remove(temp_cmd)
            with open(IP_BAK_FILE, 'w') as ipFile:
                ipFile.writelines(content)
        if 'iptables ' in cmd:
            _execute('iptables-save > %s' % IPTABLES_BAK_FILE)
    return result, errors


def _execute(cmd, process_input=None, addl_env=None, check_exit_code=True):
    LOG.debug(cmd)
    env = os.environ.copy()
    if addl_env:
        env.update(addl_env)
    obj = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    result = None
    if process_input is not None:
        result = obj.communicate(process_input)
    else:
        result = obj.communicate()
    obj.stdin.close()
    if obj.returncode:
        if check_exit_code and obj.returncode != 0:
            (stdout, stderr) = result
            raise ProcessExecutionError(exit_code=obj.returncode,
                                        stdout=utf8(stdout),
                                        stderr=utf8(stderr),
                                        cmd=cmd)
    greenthread.sleep(0)
    return result


def trycmd(*args, **kwargs):
    """
    A wrapper around execute() to more easily handle warnings and errors.

    Returns an (out, err) tuple of strings containing the output of
    the command's stdout and stderr.
    """
    discard_warnings = kwargs.pop('discard_warnings', False)

    try:
        out, err = execute(*args, **kwargs)
        failed = False
    except ProcessExecutionError as exn:
        out, err = '', str(exn)
        failed = True

    if not failed and discard_warnings and err:
        # Handle commands that output to stderr but otherwise succeed
        err = ''

    return out, err


def ssh_execute(ssh, cmd, process_input=None,
                addl_env=None, check_exit_code=True):
    LOG.debug('Running cmd (SSH): %s' % cmd)
    if addl_env:
        raise InvalidArgumentError('Environment not supported over SSH')

    if process_input:
        raise InvalidArgumentError('process_input not supported over SSH')

    stdin_stream, stdout_stream, stderr_stream = ssh.exec_command(cmd)
    channel = stdout_stream.channel

    stdout = stdout_stream.read()
    stderr = stderr_stream.read()
    stdin_stream.close()

    exit_status = channel.recv_exit_status()

    # exit_status == -1 if no exit code was returned
    if exit_status != -1:
        LOG.debug('Result was %s' % exit_status)
        if check_exit_code and exit_status != 0:
            raise ProcessExecutionError(exit_code=exit_status,
                                        stdout=stdout,
                                        stderr=stderr,
                                        cmd=cmd)

    return (stdout, stderr)


def utf8(value):
    """Try to turn a string into utf-8 if possible.
    """
    if isinstance(value, unicode):
        return value.encode("utf-8")
    assert isinstance(value, str)
    return value


def generate_mac():
    mac = [0x02, 0x00, 0x00,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))

if __name__ == '__main__':
    out, err = execute("ls -al")
    print err
    print "------------------------"
    print out
