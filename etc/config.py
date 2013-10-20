#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:config.py
# Date:Mon Sep 02 10:34:11 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com


#[service]
#agent上启用的服务。1 代表启用 ; 0 代表禁用
compute_service = 1
monitor_service = 1
ovs_service = 0

#[common]
control_br = 'br1'
data_br = 'br100'
#当设备为域间网关时需要配置对外的网桥
out_br = 'br-out'
ip = '127.0.0.1'

#Compute Service配置
#data_br: 设置本机的出口网桥
#[compute]
compute_service_bridge = data_br
compute_service_port = 8886


#Monitor 用于获取宿主及和虚拟机的状态，外界通过rpc接口获取具体的监控数据
monitor_service_port = 8887

#OVS Servie封装ovs的方法并对外提供服务，一般在ovs、controller这两类设备上需要启动该服务
ovs_service_port = 8889
controller_bin_path = '/usr/local/floodloght/target'

#[vt_manager]
vt_manager_ip = '127.0.0.1'
vt_manager_port = 8891

#[Advance]
import os


def abspath(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))
#高级配置项，一般情况下不用修改
libvirt_xml_template = abspath('../virt/libvirt.xml.template')
injected_network_template = abspath('../virt/interfaces.template')
domain_type = 'kvm'
image_path = '/var/lib/libvirt/images'
rpc_connection_timeout = 150
#libvirt相关配置
libvirt_blocking = False
