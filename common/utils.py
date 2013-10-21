#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:utils.py
# Date:Mon May 27 17:09:37 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com

"""
System-level utilities and helper functions.
"""
import traceback
import sys
import os
import signal
from eventlet.green import subprocess
from eventlet import greenthread
import random
import log as logging
LOG = logging.getLogger("agent")


def abspath(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


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


def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition('.')
    try:
        __import__(mod_str)
        return getattr(sys.modules[mod_str], class_str)
    except (ValueError, AttributeError):
        raise ImportError('Class %s cannot be found (%s)' %
                          (class_str,
                           traceback.format_exception(*sys.exc_info())))


def import_object(import_str, *args, **kwargs):
    """Import a class and return an instance of it."""
    return import_class(import_str)(*args, **kwargs)


def import_object_ns(name_space, import_str, *args, **kwargs):
    """Tries to import object from default namespace.

    Imports a class and return an instance of it, first by trying
    to find the class in a default namespace, then failing back to
    a full path if not found in the default namespace.
    """
    import_value = "%s.%s" % (name_space, import_str)
    try:
        return import_class(import_value)(*args, **kwargs)
    except ImportError:
        return import_class(import_str)(*args, **kwargs)


def import_module(import_str):
    """Import a module."""
    __import__(import_str)
    return sys.modules[import_str]


def _subprocess_setup():
    # Python installs a SIGPIPE handler by default. This is usually not what
    # non-Python subprocesses expect.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def execute(*cmd, **kwargs):
    """Helper method to execute command with optional retry.
    :param cmd:                Passed to subprocess.Popen.
    :param process_input:      Send to opened process.
    :param check_exit_code:    Single bool, int, or list of allowed exit
                               codes.  Defaults to [0].  Raise
                               exception.ProcessExecutionError unless
                               program exits with one of these code.
    :param delay_on_retry:     True | False. Defaults to True. If set to
                               True, wait a short amount of time
                               before retrying.
    :param attempts:           How many times to retry cmd.

    :raises exception.Error: on receiving unknown arguments
    :raises exception.ProcessExecutionError:

    :returns: a tuple, (stdout, stderr) from the spawned process, or None if
             the command fails.
    """

    process_input = kwargs.pop('process_input', None)
    check_exit_code = kwargs.pop('check_exit_code', [0])
    ignore_exit_code = False
    if isinstance(check_exit_code, bool):
        ignore_exit_code = not check_exit_code
        check_exit_code = [0]
    elif isinstance(check_exit_code, int):
        check_exit_code = [check_exit_code]
    delay_on_retry = kwargs.pop('delay_on_retry', True)
    attempts = kwargs.pop('attempts', 1)
    shell = kwargs.pop('shell', True)
    kwargs.pop('run_as_root', True)

    if len(kwargs):
        raise Exception(
            'Got unknown keyword args to utils.execute: %r' % kwargs)

    cmd = map(str, cmd)

    while attempts > 0:
        attempts -= 1
        try:
            LOG.debug('Running cmd (subprocess): %s' % ' '.join(cmd))
            _PIPE = subprocess.PIPE  # pylint: disable=E1101
            obj = subprocess.Popen(cmd,
                                   stdin=_PIPE,
                                   stdout=_PIPE,
                                   stderr=_PIPE,
                                   close_fds=True,
                                   shell=shell)
            result = None
            if process_input is not None:
                result = obj.communicate(process_input)
            else:
                result = obj.communicate()
            obj.stdin.close()  # pylint: disable=E1101
            _returncode = obj.returncode  # pylint: disable=E1101
            if _returncode:
                LOG.debug('Result was %s' % _returncode)
                if not ignore_exit_code and _returncode not in check_exit_code:
                    (stdout, stderr) = result
                    raise ProcessExecutionError(
                        exit_code=_returncode,
                        stdout=stdout,
                        stderr=stderr,
                        cmd=' '.join(cmd))
            return result
        except ProcessExecutionError:
            if not attempts:
                raise
            else:
                LOG.debug('%r failed. Retrying.' % cmd)
                if delay_on_retry:
                    greenthread.sleep(random.randint(20, 200) / 100.0)
        finally:
            greenthread.sleep(0)


def trycmd(*args, **kwargs):
    """
    A wrapper around execute() to more easily handle warnings and errors.

    Returns an (out, err) tuple of strings containing the output of
    the command's stdout and stderr.  If 'err' is not empty then the
    command can be considered to have failed.

    :discard_warnings   True | False. Defaults to False. If set to True,
                        then for succeeding commands, stderr is cleared

    """
    discard_warnings = kwargs.pop('discard_warnings', False)

    try:
        out, err = execute(*args, **kwargs)
        failed = False
    except ProcessExecutionError as exn:
        out, err = '', str(exn)
        LOG.debug(err)
        failed = True

    if not failed and discard_warnings and err:
        # Handle commands that output to stderr but otherwise succeed
        LOG.debug(err)
        err = ''

    return out, err


def ssh_execute(ssh, cmd, process_input=None,
                addl_env=None, check_exit_code=True):
    LOG.debug('Running cmd (SSH): %s' % ' '.join(cmd))
    if addl_env:
        raise Exception('Environment not supported over SSH')

    if process_input:
        # This is (probably) fixable if we need it...
        raise Exception('process_input not supported over SSH')

    stdin_stream, stdout_stream, stderr_stream = ssh.exec_command(cmd)
    channel = stdout_stream.channel

    # stdin.write('process_input would go here')
    # stdin.flush()

    # NOTE(justinsb): This seems suspicious...
    # ...other SSH clients have buffering issues with this approach
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
                                        cmd=' '.join(cmd))

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
