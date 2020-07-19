#!/usr/bin/env python

import atexit
import os
import sys
import ssl
import irods.exception
import unittest
import time

from irods.meta import iRODSMeta
from irods.column import Like
from irods.models import DataObject,User,DataAccess, CollectionAccess  , Collection, CollectionUser
from irods.session import iRODSSession
from irods.data_object import (irods_basename, irods_dirname , iRODSDataObject)
from irods.collection import  iRODSCollection
from irods.access import iRODSAccess

session = None

def get_session ():
    global session
    if session is None:
        try:
            env_file = os.environ['IRODS_ENVIRONMENT_FILE']
        except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
        session = iRODSSession(irods_env_file=env_file)
        atexit.register(lambda : session.cleanup() if session else None)
    return session

def coll_access_query(path) : 
  return session.query(Collection, CollectionAccess).filter(Collection.name == path)
  
def data_access_query(path) : 
  cn = irods_dirname(path)
  dn = irods_basename(path)
  return session.query(DataObject,  DataAccess).filter( Collection.name == cn, DataObject.name == dn ) 


def get_acls_on_object( obj ):

    if isinstance(obj, iRODSDataObject):
        access_column = DataAccess
        object_column = DataObject
        query_func    = data_access_query

    elif isinstance(obj, iRODSCollection):
        access_column = CollectionAccess
        object_column = Collection
        query_func    = coll_access_query

    else:
        raise TypeError

    rows  = [ r for r in query_func(obj.path) ]
    userids = set( r[access_column.user_id] for r in rows )
    
    from getusers import users_by_ids

    users_by_id = { j.id:j for j in users_by_ids(s, userids) }

    acls = [ iRODSAccess ( r[access_column.name],
                           obj.path, 
                           users_by_id[r[access_column.user_id]].name,
                           users_by_id[r[access_column.user_id]].zone  ) for r in rows ]

    return acls


if __name__ == '__main__':

    s = get_session()
    obj = None

    try:
      obj = s.data_objects.get(sys.argv[1])
    except: pass

    try:
      obj = s.collections.get(sys.argv[1])
    except: pass

    if obj:
      acls = get_acls_on_object (obj)
      import pprint
      pprint.pprint(acls)
    else :
      print('no object found')
