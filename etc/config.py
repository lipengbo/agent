#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:config.py
# Date:Mon Sep 02 10:34:11 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os


#[service]
#agent上启用的服务。1 代表启用 ; 0 代表禁用
compute_service = 1
monitor_service = 1
ovs_service = 1

#[common]
control_br = 'br100'
data_br = 'br100'
gw_br = 'br100'

#[compute service]
compute_service_port = 8886

#[monitor service]
monitor_service_port = 8887
sFlow_service = 'http://127.0.0.1:8008/'

#[ovs service]
ovs_service_port = 8889
controller_bin_path = '/usr/local/floodloght/target'

#[ccf]
ccf_ip = '127.0.0.1'
ccf_port = 8000


#[Advance]
def abspath(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))
#高级配置项，一般情况下不用修改
libvirt_xml_template = abspath('../virt/libvirt.xml.template')
injected_network_template = abspath('../virt/interfaces.template')
image_path = '/var/lib/libvirt/images/'
rpc_connection_timeout = 150
#libvirt相关配置
libvirt_blocking = False
domain_count_infinity = 1000
#dhcp相关配置
dhcp_conf = abspath('../virt/dhcp_default.conf')
dhcp_hostfile = abspath('../virt/dhcp_default.hostfile')
dhcp_conf_target = '/etc/ccf_dhcp/default.conf'
dhcp_hostfile_target = '/etc/ccf_dhcp/default.hostsfile'
