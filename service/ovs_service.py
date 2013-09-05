#!/usr/bin/env python

"""
rpcserver is an XML RPC server that allows RPC client to initiate tests
"""
import xmlrpclib
from twisted.web import xmlrpc
from ovs import util
from ovs import vswitch
from ovs import controller


class DeviceCommService(xmlrpc.XMLRPC):

    """
    This class contains all the functions that ovs-test client will call
    remotely. The caller is responsible to use designated handleIds
    for designated methods (e.g. do not mix UDP and TCP handles).
    """

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self, allowNone=True)
        self.request = None

    def render(self, request):
        """
        This method overrides the original XMLRPC.render method so that it
        would be possible to get the XML RPC client IP address from the
        request object.
        """
        self.request = request
        return xmlrpc.XMLRPC.render(self, request)

    def xmlrpc_get_my_address(self):
        """
        Returns the RPC client's IP address.
        """
        return self.request.getClientIP()

    def xmlrpc_get_my_address_from(self, his_ip, his_port):
        """
        Returns the ovs-test server IP address that the other ovs-test server
        with the given ip will see.
        """
        server1 = xmlrpclib.Server("http://%s:%u/" % (his_ip, his_port))
        return server1.get_my_address()

    def xmlrpc_create_test_bridge(self, bridge, iface):
        """
        This function creates a physical bridge from iface. It moves the
        IP configuration from the physical interface to the bridge.
        """
        ret = vswitch.ovs_vsctl_add_bridge(bridge)
        if ret == 0:
            self.pbridges.add((bridge, iface))
            util.interface_up(bridge)
            (ip_addr, mask) = util.interface_get_ip(iface)
            util.interface_assign_ip(bridge, ip_addr, mask)
            util.move_routes(iface, bridge)
            util.interface_assign_ip(iface, "0.0.0.0", "255.255.255.255")
            ret = vswitch.ovs_vsctl_add_port_to_bridge(bridge, iface)
            if ret == 0:
                self.ports.add(iface)
            else:
                util.interface_assign_ip(iface, ip_addr, mask)
                util.move_routes(bridge, iface)
                vswitch.ovs_vsctl_del_bridge(bridge)

        return ret

    def xmlrpc_del_test_bridge(self, bridge, iface):
        """
        This function deletes the test bridge and moves its IP configuration
        back to the physical interface.
        """
        ret = vswitch.ovs_vsctl_del_pbridge(bridge, iface)
        self.pbridges.discard((bridge, iface))
        return ret

    def xmlrpc_get_iface_from_bridge(self, brname):
        """
        Tries to figure out physical interface from bridge.
        """
        return vswitch.ovs_get_physical_interface(brname)

    def xmlrpc_create_bridge(self, brname):
        """
        Creates an OVS bridge.
        """
        ret = vswitch.ovs_vsctl_add_bridge(brname)
        return ret

    def xmlrpc_create_bridge_port(self, brname, port):
        """
        Creates an OVS bridge and port.
        """
        ret = vswitch.ovs_vsctl_add_bridge_port(brname, port)
        return ret

    def xmlrpc_del_bridge(self, brname):
        """
        Deletes an OVS bridge.
        """
        ret = vswitch.ovs_vsctl_del_bridge(brname)
        return ret

    def xmlrpc_is_ovs_bridge(self, bridge):
        """
        This function verifies whether given interface is an ovs bridge.
        """
        return vswitch.ovs_vsctl_is_ovs_bridge(bridge)

    def xmlrpc_add_port_to_bridge(self, bridge, port):
        """
        Adds a port to the OVS bridge.
        """
        ret = vswitch.ovs_vsctl_add_port_to_bridge(bridge, port)
        return ret

    def xmlrpc_del_port_from_bridge(self, bridge, port):
        """
        Removes a port from OVS bridge.
        """
        ret = vswitch.ovs_vsctl_del_port_from_bridge(bridge, port)
        return ret

    def xmlrpc_ovs_vsctl_set(self, table, record, column, key, value):
        """
        This function allows to alter OVS database.
        """
        return vswitch.ovs_vsctl_set(table, record, column, key, value)

    def xmlrpc_interface_up(self, iface):
        """
        This function brings up given interface.
        """
        return util.interface_up(iface)

    def xmlrpc_interface_assign_ip(self, iface, ip_address, mask):
        """
        This function allows to assing ip address to the given interface.
        """
        return util.interface_assign_ip(iface, ip_address, mask)

    def xmlrpc_get_interface(self, address):
        """
        Finds first interface that has given address
        """
        return util.get_interface(address)

    def xmlrpc_get_interface_mtu(self, iface):
        """
        Returns MTU of the given interface
        """
        return util.get_interface_mtu(iface)

    def xmlrpc_uname(self):
        """
        Return information about running kernel
        """
        return util.uname()

    def xmlrpc_get_driver(self, iface):
        """
        Returns driver version
        """
        return util.get_driver(iface)

    def xmlrpc_get_interface_from_routing_decision(self, ip):
        """
        Returns driver version
        """
        return util.get_interface_from_routing_decision(ip)

    def xmlrpc_create_controller(self, port, web_port):
        """
        Create a controller process
        """
        return controller.create_controller_process(port, web_port)

    def xmlrpc_get_dpid(self):
        """
        Get dpid of ovs
        """
        return vswitch.ovs_get_switch_dpid()

    def xmlrpc_get_bridge_list(self):
        """
        Get all the bridges in the host
        """
        return vswitch.ovs_get_bridge_list()

    def xmlrpc_get_bridge_port_list(self, bridge):
        return vswitch.ovs_get_bridge_port_list(bridge)

    def xmlrpc_set_ovs_controller(self, ip, port):
        """
        Set controller of ovs
        """
        return vswitch.set_controller(ip, port)

    def xmlrpc_get_ovs_controller(self):
        """
        Get controller of ovs
        """
        return vswitch.ovs_get_controller()

    def xmlrpc_del_ovs_controller(self):
        """
        Delete controller of ovs
        """
        return vswitch.ovs_del_controller()

    def xmlrpc_get_bridge_name(self, dpid):
        """
        Get bridge name from dpid
        """
        return vswitch.ovs_get_bridge_name(dpid)

    def xmlrpc_get_ovs_stat(self):
        """
        Get ovs statistic data
        """
        return vswitch.ovs_get_stat()

    def xmlrpc_echo(self):
        """
        Echo message for detect link state
        """
        return "echo"
