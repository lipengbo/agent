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
from sqlalchemy import Column, String, Integer, ForeignKey, create_engine, PickleType
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.event import listens_for
from etc.config import disks_mountpoint
from common import log as logging
LOG = logging.getLogger("agent.db")


engine_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent.db'))
engine = create_engine('sqlite:////%s' % engine_file)
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=engine))


class Disk(Base):
    __tablename__ = 'disk'
    id = Column(Integer, autoincrement=True, primary_key=True)
    dev = Column(String(150))
    mount_point = Column(String(255))


class Instance(Base):
    __tablename__ = 'instance'
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(String(128), unique=True)
    disk = Column(None, ForeignKey('disk.id'))
    vmInfo = Column(PickleType, nullable=True)
    sshkey = Column(String(1024), nullable=True)
    state = Column(Integer(2))


def transactional(fn):
    """add a transactional semantics to a method"""

    def transact(*args):
        session = Session()
        try:
            fn(session, *args)
            session.commit()
        except:
            session.rollback()
            raise
    transact.__name__ = fn.__name__
    return transact


def init_repository():
    Base.metadata.create_all(engine)
    session = Session()
    for dev, mountpoint in disks_mountpoint:
        record = Disk(dev=dev, mount_point=mountpoint)
        session.add(record)
    session.commit()


@listens_for(Instance, 'before_insert')
def before_insert_instance(mapper, connection, target):
    try:
        LOG.error('---------enter---before insert instance------------')
        LOG.error(mapper)
        LOG.error(connection)
        LOG.error(target.vmInfo['name'])
        LOG.error('---------leave---before insert instance------------')
    except:
        LOG.error(traceback.print_exc())


@listens_for(Instance, 'after_insert')
def after_insert_instance(mapper, connection, target):
    LOG.error('---------enter---after insert instance------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---after insert instance------------')


@listens_for(Instance, 'before_delete')
def before_delete_instance(mapper, connection, target):
    LOG.error('---------enter---before delete instance------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---before delete instance------------')


@listens_for(Instance, 'before_update')
def before_update_instance(mapper, connection, target):
    LOG.error('---------enter---before update instance------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---before update instance------------')


@listens_for(Instance, 'after_update')
def after_update_instance(mapper, connection, target):
    LOG.error('---------enter---after update instance------------')
    LOG.error(mapper)
    LOG.error(connection)
    LOG.error(target)
    LOG.error('---------leave---after update instance------------')


@transactional
def create_instance(session, *args):
    disks = session.query(Disk.id).all()
    random.shuffle(disks)
    LOG.error('---------%s------------' % type(args[0]))
    recoder = Instance(uuid=args[0]['name'], disk=disks[0][0], vmInfo=args[0], sshkey=args[1], state=args[2])
    session.add(recoder)


@transactional
def update_instance(session, *args):
    instance = session.query(Instance).filter_by(uuid=args[0]).first()
    instance.state = args[1]
    session.add(instance)


@transactional
def delete_instance(session, *args):
    instance = session.query(Instance).filter_by(uuid=args[0]).first()
    session.delete(instance)
