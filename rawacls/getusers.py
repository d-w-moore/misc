#!/usr/bin/env python

import atexit
import os
import sys
import ssl
import irods.exception
import unittest
import time
import six
import itertools
import contextlib

from irods.meta import iRODSMeta
from irods.column import Like,In
from irods.models import DataObject,User,DataAccess, CollectionAccess, Collection, CollectionUser
from irods.session import iRODSSession
from irods.data_object import (irods_basename, irods_dirname)
from irods.user import (iRODSUser)

def yield_session ():
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
        env_file = os.path.expanduser('~/.irods/irods_environment.json')
    session = iRODSSession(irods_env_file=env_file)
    try:
        yield session
    finally:
        pass # session.cleanup()

c_yield_session = contextlib.contextmanager(yield_session)

def users_by_ids(session,ids=()) : 
  try:
    ids=list(iter(ids))
  except TypeError:
    if type(ids) in (str,)+six.integer_types: ids=int(ids)
    else: raise
  cond = () if not ids \
         else (In(User.id,list(map(int,ids))),) if len(ids)>1 \
         else (User.id == int(ids[0]),)
  return [ iRODSUser(session.users,i) 
           for i in session.query(User.id,User.name,User.type,User.zone).filter(*cond) ]

if __name__ == '__main__':
  with c_yield_session() as s:
    import pprint
    j =  users_by_ids(s)
    #ji = iter( j )
    #while ji: #__ peel off list of 5 at a time
    #  jl = list(itertools.islice(ji,5))
    #  pprint.pprint(jl)
    #  if not jl: ji =None
    if 1:
      print('all user/group =',users_by_ids(s,(i.id for i in j)))
      pprint.pprint( users_by_ids(s))
      print('----')
      pprint.pprint([ (i.name,i.zone,i.type) for i in users_by_ids(s,(10002L,'10029'))])
