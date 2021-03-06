#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:config.py
# Date:Mon Sep 02 10:34:11 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os


#[service]
# agent上启用的服务。1 代表启用 ; 0 代表禁用
compute_service = 1
monitor_service = 1
ovs_service = 1
vpn_service = 1

#[common]
control_br = 'br1'
data_br = 'br0'
gw_br = control_br

#[compute service]
compute_service_port = 8886

#[monitor service]
monitor_service_port = 8887
sFlow_service = 'http://192.168.5.24:8008/'

#[ovs service]
ovs_service_port = 8889
controller_bin_path = '/usr/local/floodloght/target'

#[vpn service]
vpn_service_port = 8890

#[ccf]
ccf_ip = '192.168.5.45'
ccf_port = 8000


#[Advance]
def abspath(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))
# 高级配置项，一般情况下不用修改
libvirt_xml_template = abspath('../virt/libvirt.xml.template')
injected_network_template = abspath('../virt/interfaces.template')
rpc_connection_timeout = 150
# libvirt相关配置
libvirt_blocking = False
domain_count_infinity = 1000
# dhcp相关配置
dhcp_conf = abspath('../virt/dhcp_default.conf')
dhcp_hostfile = abspath('../virt/dhcp_default.hostfile')
dhcp_conf_target = '/etc/ccf_dhcp/default.conf'
dhcp_hostfile_target = '/etc/ccf_dhcp/default.hostsfile'

#[Disk]
# 配置image保存的基本路径
image_path = '/var/lib/libvirt/images/'
# 多磁盘及其挂载点配置
disks_mountpoint = [('/dev/sda1', image_path + 'disk1/'),
                    ('/dev/sdb', image_path + 'disk2/'),
                    ('/dev/sdc', image_path + 'disk3/'),
                    ('/dev/sdd', image_path + 'disk4/'),
                    ]
