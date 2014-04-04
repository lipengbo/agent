#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:table_define.py
# Date:三  4月 02 14:10:24 CST 2014
# Author:Pengbo Li
# E-mail:lipengbo10054444@gmail.com
import os
import random
import traceback
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref
from sqlalchemy.event import listens_for
from etc.config import disks_mountpoint
from common import log as logging
LOG = logging.getLogger("agent.db")


engine_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent.db'))
engine = create_engine('sqlite:////%s' % engine_file)
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=engine))


def init_repository():
    Base.metadata.create_all(engine)
    session = Session()
    for dev, mountpoint in disks_mountpoint:
        record = Disk(dev=dev, mount_point=mountpoint)
        session.add(record)
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
    mem = Column(Integer)
    cpus = Column(Integer)
    hdd = Column(Integer, default=10)
    base_image = Column(String(128))
    glance_url = Column(String(1024))
    sshkey = Column(String(1024), nullable=True)
    vm_type = Column(Integer(2), default=1)
    disk_dev = Column(Integer, ForeignKey('disk.dev'))
    disk = relationship(Disk, backref=backref('domain', order_by=name))
    state = Column(Integer(2))

    @transactional
    def save(self, session, *args):
        self.disk = Disk.get_suitable_disk()
        session.add(self)

    @transactional
    def update(self, session, *args):
        name = args[0]
        domain = session.query(Domain).filter_by(uuid=name).first()
        domain.state = args[1]
        session.add(domain)

    @transactional
    def delete_domain(session, *args):
        name = args[0]
        domain = session.query(Domain).filter_by(uuid=name).first()
        session.delete(domain)


@listens_for(Domain, 'before_insert')
def before_insert_domain(mapper, connection, target):
    try:
        LOG.error('---------enter---before insert domain------------')
        LOG.error(mapper)
        LOG.error(connection)
        LOG.error(target.vmInfo['name'])
        LOG.error('---------leave---before insert domain------------')
    except:
        LOG.error(traceback.print_exc())


@listens_for(Domain, 'after_insert')
def after_insert_domain(mapper, connection, target):
    LOG.error('---------enter---after insert domain------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---after insert domain------------')


@listens_for(Domain, 'before_update')
def before_update_domain(mapper, connection, target):
    LOG.error('---------enter---before update domain------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---before update domain------------')


@listens_for(Domain, 'after_update')
def after_update_domain(mapper, connection, target):
    LOG.error('---------enter---after update domain------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---after update domain------------')


@listens_for(Domain, 'before_delete')
def before_delete_domain(mapper, connection, target):
    LOG.error('---------enter---before delete domain------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---before delete domain------------')
