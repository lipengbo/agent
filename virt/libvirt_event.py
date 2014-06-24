#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:libvirt_event_test.py
# Date:Tue May 27 11:11:54 CST 2014
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import libvirt
import threading
from service.compute import ComputeManager


def eventToString(event):
    eventStrings = ("Defined",
                    "Undefined",
                    "Started",
                    "Suspended",
                    "Resumed",
                    "Stopped",
                    "Shutdown",
                    "PMSuspended")
    return eventStrings[event]


def detailToString(event, detail):
    eventStrings = (
        ("Added", "Updated"),
        ("Removed", ),
        ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup"),
        ("Paused", "Migrated", "IOError", "Watchdog",
         "Restored", "Snapshot", "API error"),
        ("Unpaused", "Migrated", "Snapshot"),
        ("Shutdown", "Destroyed", "Crashed",
         "Migrated", "Saved", "Failed", "Snapshot"),
        ("Finished", ),
        ("Memory", "Disk"))
    return eventStrings[event][detail]


def myDomainEventCallback1(conn, dom, event, detail, opaque):
    #print "myDomainEventCallback1 EVENT: Domain: %s Event: %s Detail: %s" % (dom.name(), eventToString(event), detailToString(event, detail))
    if event == 5:
        ComputeManager._set_domain_state(dom.name(), state=event)
    if event == 3:
        ComputeManager._set_domain_state(dom.name(), state=event)
    if event == 2 and detailToString(event, detail) == "Snapshot":
        ComputeManager._set_domain_state(dom.name(), state=1)


def virEventLoopNativeRun():
    while True:
        libvirt.virEventRunDefaultImpl()


def virEventLoopNativeStart():
    libvirt.virEventRegisterDefaultImpl()
    eventLoopThread = threading.Thread(
        target=virEventLoopNativeRun, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


def domainEventThread():
    uri = "qemu:///system"
    virEventLoopNativeStart()
    conn = libvirt.open(uri)
    #conn.domainEventRegister(myDomainEventCallback1, None)
    conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, myDomainEventCallback1, None)
