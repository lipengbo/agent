#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:install.py
# Date:五 12月 27 09:37:04 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
import sys
sys.path.insert(0, '../')
from common import utils


AGENTHOME = os.path.abspath(os.path.pardir)
libvirt_init_file = os.path.join(AGENTHOME, 'etc/init/libvirt-bin.conf')
ln_libvirt_init_file = os.path.abspath('/etc/init/libvirt-bin.conf')
ln_libvirt_cmd = 'ln -s %s %s' % (libvirt_init_file, ln_libvirt_init_file)

agent_init_file = os.path.join(AGENTHOME, 'etc/init/ccf-agent.conf')
ln_agent_init_file = os.path.abspath('/etc/init/ccf-agent.conf')
ln_agent_cmd = 'ln -s %s %s' % (agent_init_file, ln_agent_init_file)

vswitchd_init_file = os.path.join(AGENTHOME, 'etc/init/ovs-vswitchd.conf')
ln_vswitched_init_file = os.path.abspath('/etc/init/ovs-vswitchd.conf')
ln_vswitched_cmd = 'ln -s %s %s' % (vswitchd_init_file, ln_vswitched_init_file)

ovsdb_init_file = os.path.join(AGENTHOME, 'etc/init/ovsdb-server.conf')
ln_ovsdb_init_file = os.path.abspath('/etc/init/ovsdb-server.conf')
ln_ovsdb_cmd = 'ln -s %s %s' % (ovsdb_init_file, ln_ovsdb_init_file)


new_agent_home = os.path.abspath('/usr/local/agent')
ln_agent_dir_cmd = 'ln -s %s %s' % (AGENTHOME, new_agent_home)

print sys.argv
if len(sys.argv) == 2:
    if sys.argv[1] == 'install':
        utils.execute(ln_libvirt_cmd)
        print 'libvirt-bin.conf success'
        utils.execute(ln_agent_cmd)
        print 'ccf-agent.conf success'
        utils.execute(ln_vswitched_cmd)
        print 'ovs-vswitchd.conf success'
        utils.execute(ln_ovsdb_cmd)
        print 'ovsdb-server.conf success'
        utils.execute(ln_agent_dir_cmd)
        print 'agent.conf success'
    elif sys.argv[1] == 'uninstall':
        print ln_libvirt_init_file
        if os.path.exists(ln_libvirt_init_file):
            os.remove(ln_libvirt_init_file)
        print ln_agent_init_file
        if os.path.exists(ln_agent_init_file):
            os.remove(ln_agent_init_file)
        print ln_vswitched_init_file
        if os.path.exists(ln_vswitched_init_file):
            os.remove(ln_vswitched_init_file)
        print ln_ovsdb_init_file
        if os.path.exists(ln_ovsdb_init_file):
            os.remove(ln_ovsdb_init_file)
        print new_agent_home
        if os.path.exists(new_agent_home):
            os.remove(new_agent_home)
    else:
        print 'unknown option, install|uninstall'
        return
    init_cmd = 'initctl reload-configuration'
    utils.execute(init_cmd)
else:
    print 'usage: python setup.py install|uninstall'
