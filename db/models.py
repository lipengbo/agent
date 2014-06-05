#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:table_define.py
# Date:三  4月 02 14:10:24 CST 2014
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
import random
from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy import ForeignKey
#from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
#from etc.config import disks_mountpoint
from common import log as logging
LOG = logging.getLogger("agent.db")


engine_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent.db'))
engine = create_engine('sqlite:////%s' % engine_file)
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=engine))


def init_repository():
    Base.metadata.create_all(engine)
    session = Session()
    #for dev, mountpoint in disks_mountpoint:
        #record = Disk(dev=dev, mount_point=mountpoint)
        #session.add(record)
    session.commit()


def transactional(fn):
    """add a transactional semantics to a method"""

    def transact(self, *args):
        session = Session()
        try:
            fn(self, session, *args)
            session.commit()
        except:
            session.rollback()
            raise
    transact.__name__ = fn.__name__
    return transact


class Disk(Base):
    __tablename__ = 'disk'
    dev = Column(String(150), primary_key=True)
    mount_point = Column(String(255))

    @classmethod
    @transactional
    def get_all_disks(cls, session, *args):
        print '-------------------'
        print cls
        print type(cls)
        print session
        print args
        disks = session.query(cls).all()
        print disks
        print '-------------------'
        return disks

    @classmethod
    @transactional
    def get_suitable_disk(cls, session, *args):
        disks = cls.get_all_disks()
        random.shuffle(disks)
        return disks


class Domain(Base):
    __tablename__ = 'domain'
    name = Column(String(128), primary_key=True)
    #mem = Column(Integer, nullable=True)
    #cpus = Column(Integer, nullable=True)
    #hdd = Column(Integer, default=10)
    #base_image = Column(String(128), nullable=True)
    #glance_url = Column(String(1024), nullable=True)
    #sshkey = Column(String(1024), nullable=True)
    #vm_type = Column(Integer(2), default=1)
    #disk_dev = Column(Integer, ForeignKey('disk.dev'))
    #disk = relationship(Disk, backref=backref('domain', order_by=name))
    ofport = Column(Integer(5), nullable=True)
    state = Column(Integer(2))

    @transactional
    def save(self, session, *args):
        session.add(self)

    @classmethod
    @transactional
    def update(cls, session, *args):
        name = args[0]
        ofport = args[1]
        state = args[2]
        domain = session.query(cls).filter_by(name=name).first()
        if ofport:
            domain.ofport = ofport
        if state:
            domain.state = state
        session.add(domain)

    @classmethod
    @transactional
    def delete(cls, session, *args):
        name = args[0]
        domain = session.query(cls).filter_by(name=name).first()
        session.delete(domain)

    @classmethod
    @transactional
    def start_vms(cls, session, func):
        domains = session.query(cls).filter_by(state=2)
        for dom in domains:
            func(dom.name, 'create', dom.ofport)
