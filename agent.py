#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:agent.py
# Date:Sat Jul 06 11:55:55 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com


def start_service():
    import traceback
    from twisted.internet import reactor
    from twisted.web import server
    from service.ovs_service import DeviceCommService
    from service.monitor import MonitorService
    from service.compute import ComputeService, ComputeManager
    from service.vpn_tools import VPNService
    from db.models import Domain
    from etc import config
    from virt.libvirt_event import domainEventThread
    from common import log as logging
    LOG = logging.getLogger("agent.virt")

    if config.compute_service:
        service = server.Site(ComputeService())
        reactor.listenTCP(config.compute_service_port, service)
    if config.ovs_service:
        service = server.Site(DeviceCommService())
        reactor.listenTCP(config.ovs_service_port, service)
    if config.monitor_service:
        service = server.Site(MonitorService())
        reactor.listenTCP(config.monitor_service_port, service)
    if config.vpn_service:
        service = server.Site(VPNService())
        reactor.listenTCP(config.vpn_service_port, service)
    try:
        domainEventThread()
        Domain.start_vms(ComputeManager.start_vms)
        reactor.run()
    except Exception:
        LOG.error(traceback.print_exc())


import os
import sys
import time
import atexit
import gflags
from signal import SIGTERM
FLAGS = gflags.FLAGS
gflags.DEFINE_boolean('daemon', True, 'whether daemon the proccess')
gflags.DEFINE_string('pidfile', '/var/run/ccf-agent.pid', 'whether daemon the proccess')


class AgentDaemon(object):

    def __init__(self, pidfile, daemon):
        self.pidfile = pidfile
        self.daemon = daemon
        if self.daemon:
            self.stdin = '/dev/null'
            self.stdout = '/dev/null'
            self.stderr = '/dev/null'
        else:
            self.stdin = sys.stdin
            self.stdout = sys.stdout
            self.stderr = sys.stderr

    def delpidfile(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def _fork(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stdout.write(str(e))
            sys.exit(1)

    def daemonize(self):
        self._fork()
        os.chdir('./')
        os.setsid()
        os.umask(0)
        self._fork()
        atexit.register(self.delpidfile)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write('%s\n' % pid)
        #设置打印信息不要打印出来
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def start(self):
        if self.daemon:
            self.daemonize()
        start_service()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        self.stop()
        self.start()


if __name__ == '__main__':
    argv = FLAGS(sys.argv)
    if len(argv) == 2:
        agent = AgentDaemon(FLAGS.pidfile, FLAGS.daemon)
        if argv[1] == 'start':
            agent.start()
        elif argv[1] == 'stop':
            agent.stop()
        elif argv[1] == 'restart':
            agent.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
