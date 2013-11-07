#coding:utf-8
'''
Created on 2013年5月23日

@author: hexiaoxi
'''
from common.xmlrpcclient import get_rpc_client
from etc import config


# 设置控制器
def set_controller(ovs_ip, controller_ip, controller_port):
    success = True
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        success = client.set_ovs_controller(controller_ip, controller_port)
    except:
        success = False
    return success


# 获取控制器
def get_controller(ovs_ip):
    """
    获取交换机的控制器
        成功返回 tuple(ip, port)，失败返回 None
    """
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_ovs_controller()
    except:
        pass
    return None


# 删除控制器
def del_controller(ovs_ip):
    success = True
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        success = client.del_ovs_controller()
    except:
        success = False
    return success


# 添加网桥
def add_bridge(ovs_ip, bridge):
    success = True
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        success = (client.create_bridge(bridge) == 0)
    except:
        success = False
    return success


# 同时添加网桥和端口
def add_bridge_port(ovs_ip, bridge, port):
    success = True
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        success = (client.create_bridge_port(bridge, port) == 0)
    except:
        success = False
    return success


# 删除网桥
def del_bridge(ovs_ip, bridge):
    success = True
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        success = (client.del_bridge(bridge) == 0)
    except:
        success = False
    return success


# 添加端口
def add_port(ovs_ip, bridge, port):
    success = True
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        success = (client.add_port_to_bridge(bridge, port) == 0)
    except:
        success = False
    return success


# 删除端口
def del_port(ovs_ip, bridge, port):
    success = True
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        success = (client.del_port_from_bridge(bridge, port) == 0)
    except:
        success = False
    return success


# 获取交换机DPID。选取设置了控制器的网桥DPID作为交换机的DPID。
def get_dpid(ovs_ip):
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_dpid()
    except:
        pass
    return None


# 根据DPID获取网桥名称
def get_bridge_name(ovs_ip, dpid):
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_bridge_name(dpid)
    except:
        pass
    return None


# 获取交换机统计数据
def get_switch_stat(ovs_ip):
    try:
        print ovs_ip
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_ovs_stat()
    except:
        pass
    return None


def get_bridge_list(ovs_ip):
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_bridge_list()
    except:
        pass
    return None


def get_bridge_port_list(ovs_ip, bridge):
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_bridge_port_list(bridge)
    except:
        pass
    return None


def get_portid_by_name(ovs_ip, port_name):
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_portid_by_name(port_name)
    except:
        pass
    return None


def get_sFlow_metric(ovs_ip, dpid, ofport, maclist):
    """
        maclist: It's a list of mac,but word must supper and no : in the string.eg: ['525400B9FA73']
    """
    try:
        client = get_rpc_client(ovs_ip, config.ovs_service_port)
        return client.get_sFlow_metric(ovs_ip, dpid, ofport, maclist)
    except:
        pass
    return None
