# coding:utf-8
'''
Created on 2013年5月24日

@author: hexiaoxi
'''
from ovs import util
from etc import config
import time

"""
controller module allows its callers to interact with OpenFlow controller.
"""


def create_controller_process(port, web_port):
    if util.is_port_exist("tcp.*:%d" % port) or util.is_port_exist("tcp.*:%d" % web_port):
        return (False, -1)
    java_cmd = [
        "java", "-Dnet.floodlightcontroller.core.FloodlightProvider.openflowport=%d" % port,
                "-Dnet.floodlightcontroller.restserver.RestApiServer.port=%d" % web_port,
        "-Dnet.floodlightcontroller.jython.JythonDebugInterface.port=0",
        "-jar", "%s/floodlight.jar" % config.controllerBinDir]
    _ret = util.start_bg_process(java_cmd)
    if _ret != 0:
        return (False, -2)
    # Check if the floodlight process is listening the port
    waitOnceTime = 2
    waitTotalTime = waitOnceTime
    time.sleep(waitOnceTime)  # Wait seconds
    while True:
        if not util.is_port_exist("tcp.*:%d.*java" % port) or not util.is_port_exist("tcp.*:%d.*java" % web_port):
            # Listening failed, kill the floodlight process
            if waitTotalTime > 32:
                cmd = 'ps -ef|grep "openflowport=%d.*floodlight"|grep -v grep|awk \'{printf $2}\'|xargs kill -9' % port
                _ret, _out, _err = util.start_process(cmd, shell=True)
                return (False, -3)
            else:
                waitOnceTime *= 2
                time.sleep(waitOnceTime)
                waitTotalTime += waitOnceTime
        else:
            break

    return (True, 0)
