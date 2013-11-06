#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:sflow_proxy.py
# Date:四 11月 07 01:04:09 CST 2013
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import json
from common import utils
from etc.config import sFlow_service


class SFlow_Proxy(object):

    @staticmethod
    def get_ifindex_by_ofport(dpid, ofport):
        br_port_list = SFlow_Proxy.get_ports_name_by_dpid(dpid)
        for port_name in br_port_list:
            ofport_tmp = SFlow_Proxy.get_ofport_by_port_name(port_name)
            if str(ofport) == ofport_tmp:
                return SFlow_Proxy.get_ifindex_by_port_name(port_name)
        return None

    @staticmethod
    def set_sFlow_metric_event(dpid, ofport, maclist):
        for mac in maclist:
            #url = sFlow_service + 'flow/' + \
                #'%s_%s_%s_in' % (dpid, ofport, mac) + '/json'
            header = "\"Content-Type:application/json\""
            data = "\"{keys:'ipsource,ipdestination',value:'bytes',filter:'macdestination=%s'}\"" % mac
            #in_cmd = "curl -H " + header + \
                #" -X PUT --data " + data + " " + url
            url = sFlow_service + 'flow/' + \
                '%s_%s_%s_out' % (dpid, ofport, mac) + '/json'
            data = "\"{keys:'ipsource,ipdestination',value:'bytes',filter:'macsource=%s'}\"" % mac
            out_cmd = "curl -H " + header + \
                " -X PUT --data " + data + " " + url
            #utils.execute(in_cmd)
            utils.execute(out_cmd)

    @staticmethod
    def get_sFlow_metric_event(agentip, dpid, ofport, maclist):
        ifindex = SFlow_Proxy.get_ifindex_by_ofport(dpid, ofport)
        ifspeed = None
        if_used_speed = 0
        for mac in maclist:
            #url = sFlow_service + 'metric/' + agentip + "/" + '%s_%s_%s_in' % (dpid, ofport, mac) + '/json'
            #in_cmd = "curl " + url
            #url = sFlow_service + 'metric/' + agentip + "/" + '%s_%s_%s_out' % (dpid, ofport, mac) + '/json'
            uri = '%s_%s_%s_out' % (dpid, ofport, mac)
            key = '%s.%s' % (ifindex, uri)
            url = sFlow_service + 'metric/' + agentip + '/json'
            out_cmd = "curl " + url
            #out, err = utils.execute(in_cmd)
            out, err = utils.execute(out_cmd)
            out = json.loads(out)
            out_speed = out.get(key.lower(), 0)
            if_used_speed = if_used_speed + out_speed
            if not ifspeed:
                ifspeed = out.get('%s.ifspeed' % ifindex, None)
        return ifspeed, if_used_speed

    @staticmethod
    def get_ports_name_by_dpid(dpid):
        out, err = utils.execute(
            'br=`ovs-vsctl --bare -- --columns=name find bridge datapath_id=%s`;ovs-vsctl list-ports $br' % dpid)
        ports_name = map(lambda x: x.strip(), out.strip().split())
        return ports_name

    @staticmethod
    def get_ofport_by_port_name(port_name):
        out, err = utils.execute(
            'ovs-vsctl get interface %s ofport' % port_name)
        ofport = out.strip()
        return ofport

    @staticmethod
    def get_ifindex_by_port_name(port_name):
        out, err = utils.execute(
            "ip link ls %s|awk -F ':' 'NR==1{print $1}'" % port_name)
        ifindex = out.strip()
        return ifindex
