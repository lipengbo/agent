# coding:utf-8
# Copyright (c) 2012 Nicira, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from etc import config
import re

"""
vswitch module allows its callers to interact with OVS DB.
"""

from ovs import util


def ovs_vsctl_add_bridge(bridge):
    """
    This function creates an OVS bridge.
    """
    ret, _out, _err = util.start_process(["ovs-vsctl", "--", "--may-exist", "add-br", bridge])
    return ret


def ovs_vsctl_add_bridge_port(bridge, port):
    """
    This function creates an OVS bridge and add port.
    """
    ret, _out, _err = util.start_process(["ovs-vsctl", "add-br", bridge, "--",
                                          "add-port", bridge, port])
    return ret


def ovs_vsctl_del_bridge(bridge):
    """
    This function deletes the OVS bridge.
    """
    ret, _out, _err = util.start_process(
        ["ovs-vsctl", "--", "--if-exists", "del-br", bridge])
    return ret


def ovs_vsctl_del_pbridge(bridge, iface):
    """
    This function deletes the OVS bridge and assigns the bridge IP address
    back to the iface.
    """
    (ip_addr, mask) = util.interface_get_ip(bridge)
    util.interface_assign_ip(iface, ip_addr, mask)
    util.move_routes(bridge, iface)
    return ovs_vsctl_del_bridge(bridge)


def ovs_vsctl_is_ovs_bridge(bridge):
    """
    This function verifies whether given port is an OVS bridge. If it is an
    OVS bridge then it will return True.
    """
    ret, _out, _err = util.start_process(["ovs-vsctl", "br-exists", bridge])
    return ret == 0


def ovs_vsctl_add_port_to_bridge(bridge, iface):
    """
    This function adds given interface to the bridge.
    """
    ret, _out, _err = util.start_process(["ovs-vsctl", "--", "--may-exist", "add-port", bridge,
                                          iface])
    return ret


def ovs_vsctl_del_port_from_bridge(bridge, port):
    """
    This function removes given port from a OVS bridge.
    """
    ret, _out, _err = util.start_process(
        ["ovs-vsctl", "--", "--if-exists", "del-port",
         bridge, port])
    return ret


def ovs_vsctl_set(table, record, column, key, value):
    """
    This function allows to alter the OVS database. If column is a map, then
    caller should also set the key, otherwise the key should be left as an
    empty string.
    """
    if key is None:
        index = column
    else:
        index = "%s:%s" % (column, key)
    index_value = "%s=%s" % (index, value)
    ret, _out, _err = util.start_process(["ovs-vsctl", "set", table, record,
                                          index_value])
    return ret


def ovs_get_physical_interface(bridge):
    """
    This function tries to figure out which is the physical interface that
    belongs to the bridge. If there are multiple physical interfaces assigned
    to this bridge then it will return the first match.
    """
    ret, out, _err = util.start_process(["ovs-vsctl", "list-ifaces", bridge])

    if ret == 0:
        ifaces = out.splitlines()
        for iface in ifaces:
            ret, out, _err = util.start_process(["ovs-vsctl", "get",
                                                 "Interface", iface, "type"])
            if ret == 0:
                if ('""' in out) or ('system' in out):
                    return iface  # this should be the physical interface
    return None


def ovs_get_bridge_name(dpid):
    """
    获取dpid对应的网桥名称。
    """
    ret, out, _err = util.start_process(["ovs-vsctl", "list-br"])
    if ret == 0:
        brs = out.splitlines()
        for br in brs:
            ret, out, _err = util.start_process(["ovs-vsctl", "get", "bridge",
                                                 br, "datapath_id"])
            if ret == 0 and out.replace('"', '') == dpid:
                return br
    return None


def ovs_set_bridge_dpid(bridge, dpid):
    ret, out, _err = util.start_process(["ovs-vsctl", "set", "bridge", bridge, "other_config:datapath-id=%s" % dpid])
    return ret


def ovs_get_bridge_list():
    ret, out, _err = util.start_process(["ovs-vsctl", "list-br"])
    if ret == 0:
        brs = out.splitlines()
        return brs
    return None


def ovs_get_bridge_port_list(bridge):
    ret, out, _err = util.start_process(["ovs-vsctl", "list-ports", bridge])
    if ret == 0:
        brs = out.splitlines()
        return brs
    return None


def ovs_get_controller_bridge():
    """
    获取交换机上与控制器连接的网桥，确定网桥依据是网桥所对应的网卡设置了IP地址已经设置了控制器。
    """
    # 检查是否有网桥设置了控制器
    ret, out, _err = util.start_process(["ovs-vsctl", "list-br"])
    if ret == 0:
        brs = out.splitlines()
        for br in brs:
            ret, out, _err = util.start_process(["ovs-vsctl", "get-controller",
                                                 br])
            if ret == 0:
                if out != "":
                    return br

    # 检查是否有网桥的网卡设置了IP地址
    ret, out, _err = util.start_process(
        ["ovs-vsctl", "--", "--columns=name", "list", "Interface"])

    if ret == 0:
        matchs = re.finditer(r"\"(.*?)\"", out, re.DOTALL)
        for match in matchs:
            iface = match.group(1)
            ret, out, _err = util.start_process(["ovs-vsctl", "get",
                                                 "Interface", iface, "type"])
            if ret == 0:
                if ('""' in out) or ('system' in out):
                    # 网卡为物理网卡，判断其是否设置了IP地址
                    ret, out, _err = util.start_process(
                        "ifconfig %s" % iface, shell=True)
                    if ret == 0:
                        pattern = ("inet .*?:((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])"
                                   "\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)"
                                   "\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)"
                                   "\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9]))")
                        m = re.search(pattern, out, re.DOTALL)
                        if m:
                            ret, out, _err = util.start_process(
                                ["ovs-vsctl", "iface-to-br", iface])
                            if ret == 0:
                                return ''.join(out.split())
    return None


def ovs_get_switch_dpid():
    """
    获取交换机上与控制器连接的网桥的DPID。
    """
    bridge = ovs_get_controller_bridge()
    if not bridge:
        bridge = config.data_br
    ret, out, _err = util.start_process(["ovs-vsctl", "get", "bridge", bridge, "datapath_id"])
    if ret == 0:
        return ''.join(out.split()).replace('"', '')
    return None


def set_controller(ip, port):
    """
    设置交换机的控制器，选择设置控制器的网桥依据是该网桥网卡设置了IP地址或已经设置了控制器。
    """
    bridge = ovs_get_controller_bridge()
    if bridge:
        ret, _out, _err = util.start_process(
            ["ovs-vsctl", "set-controller", bridge,
             "tcp:%s:%d" % (ip, port)])
        return ret == 0
    return False


def ovs_get_controller():
    """
    获取交换机的控制器
    """
    ret, out, _err = util.start_process(["ovs-vsctl", "list-br"])
    if ret == 0:
        brs = out.splitlines()
        for br in brs:
            ret, out, _err = util.start_process(["ovs-vsctl", "get-controller",
                                                 br])
            if ret == 0:
                if out != "":
                    ip_port = out[0:-1].split(':')[1:]
                    return (ip_port[0], int(ip_port[1]))
    return None


def ovs_del_controller():
    """
    删除交换机的控制器
    """
    ret, out, _err = util.start_process(["ovs-vsctl", "list-br"])
    if ret == 0:
        brs = out.splitlines()
        for br in brs:
            ret, out, _err = util.start_process(["ovs-vsctl", "get-controller",
                                                 br])
            if ret == 0:
                if out != "":
                    ret, out, _err = util.start_process(
                        ["ovs-vsctl", "del-controller",
                         br])
                    if ret == 0:
                        return True
    return False


def ovs_get_stat():
    """
    获取交换机的统计数据
    """
    ret, out, _err = util.start_process(["ovs-vsctl", "list-br"])
    if ret == 0:
        data = []
        brs = out.splitlines()
        for br in brs:
            bridge = {'name': br}
            cmd = 'netstat -apn|grep "vswitchd.*%s.mgmt"|awk \'{print $NF}\'' % br
            ret, brfile, _err = util.start_process(cmd, shell=True)
            brfile = ''.join(brfile.split())
            if ret == 0 and brfile != "":
                # 获取端口列表
                ret, out, _err = util.start_process(
                    ["ovs-ofctl", "dump-ports-desc",
                     brfile])
                if ret == 0 and out != "":
                    """
                    dump-ports-desc命令返回内容：

                     3(patch02): addr:ce:a9:6d:9c:e2:0a
                     config:     0
                     state:      0
                     speed: 100 Mbps now, 100 Mbps max

                    """
                    matches = re.finditer(
                        "\n.*?\((.*?)\): addr:(.*?)\n.*?state:\s*(.*?)\n",
                        out, re.DOTALL | re.MULTILINE)
                    ports = []
                    for m in matches:
                        # 获取端口状态和统计数据
                        port = {
                            'name': m.group(1),
                            'mac': m.group(2),
                            'state': m.group(3)
                        }
                        """
                        dump-ports命令返回内容：

                          port 65534: rx pkts=0, bytes=0, drop=0, errs=0, frame=0, over=0, crc=0
                          tx pkts=0, bytes=0, drop=0, errs=0, coll=0

                        """
                        print 'port:', port['name']
                        ret, out, _err = util.start_process(
                            ["ovs-ofctl", "dump-ports",
                             brfile, port['name']])
                        if ret == 0 and out != "":
                            stats = re.search(("rx pkts=([0-9]+), bytes=([0-9]+), drop=([0-9]+)"
                                               ", errs=([0-9]+), frame=([0-9]+), over=([0-9]+)"
                                               ", crc=([0-9]+).*tx pkts=([0-9]+), bytes=([0-9]+)"
                                               ", drop=([0-9]+), errs=([0-9]+), coll=([0-9]+)"),
                                              out, re.DOTALL | re.MULTILINE)
                            if stats:
                                rx = {
                                    '包': stats.group(1), 'byte': stats.group(2),
                                    '丢包': stats.group(3), '错误': stats.group(4),
                                    '帧错误': stats.group(5), '包溢出': stats.group(6),
                                    'CRC错误': stats.group(7)
                                }
                                tx = {
                                    '包': stats.group(8), 'byte': stats.group(9),
                                    '丢包': stats.group(10), '冲突': stats.group(11)
                                }
                                port['stats'] = {'recv': rx,
                                                 'send': tx
                                                 }

                        ports.append(port)

                    bridge['ports'] = ports
                data.append(bridge)
        return data
    return None
