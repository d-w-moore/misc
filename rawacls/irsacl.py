#!/usr/bin/env python
from __future__ import print_function
import atexit
import os
import sys
import ssl
import irods.exception
import unittest
import time
import pprint

from irods.meta import iRODSMeta
from irods.models import (DataObject, User, DataAccess, CollectionAccess, Collection, CollectionUser)
from irods.session import iRODSSession
from irods.data_object import (irods_basename, irods_dirname , iRODSDataObject)
from irods.collection import  iRODSCollection
from irods.access import iRODSAccess
from irods.column import In
from irods.user import iRODSUser

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


def coll_access_query(session,path):
  return session.query(Collection, CollectionAccess).filter(Collection.name == path)

def data_access_query(session,path):
  cn = irods_dirname(path)
  dn = irods_basename(path)
  return session.query(DataObject,  DataAccess).filter( Collection.name == cn, DataObject.name == dn )

def users_by_ids(session,ids=()) :
  try:
    ids=list(iter(ids))
  except TypeError:
    if type(ids) in (str,) + six.integer_types: ids=int(ids)
    else: raise
  cond = () if not ids \
         else (In(User.id,list(map(int,ids))),) if len(ids)>1 \
         else (User.id == int(ids[0]),)
  return [ iRODSUser(session.users,i)
           for i in session.query(User.id,User.name,User.type,User.zone).filter(*cond) ]

def get_acls_on_object( sess, obj , **kw ):

    users_out = kw.pop( 'acl_users', None )
    T = kw.pop( 'acl_users_transform', lambda value : value )

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

    rows  = [ r for r in query_func(sess, obj.path) ]
    userids = set( r[access_column.user_id] for r in rows )

    user_lookup = { j.id:j for j in users_by_ids(sess, userids) }

    if isinstance(users_out, dict):     users_out.update (user_lookup)
    elif isinstance (users_out, list):  users_out += [T(v) for v in user_lookup.values()]
    elif isinstance (users_out, set):   users_out |= set(T(v) for v in user_lookup.values())
    elif users_out is None: pass
    else:                   raise TypeError

    acls = [ iRODSAccess ( r[access_column.name],
                           obj.path,
                           user_lookup[r[access_column.user_id]].name,
                           user_lookup[r[access_column.user_id]].zone  ) for r in rows ]
    return acls


def main(sess, u=None):
    obj = None
    if u is not None: ulst = eval(u)
    for tp in ['data object','collection']:
        if tp == 'data object':
            try:
                obj = sess.data_objects.get(sys.argv[1])
            except: pass
        elif tp == 'collection':
            try:
                obj = sess.collections.get(sys.argv[1])
            except: pass

        if obj:
            kw  = { 'acl_users': ulst,
                   #'acl_users_transform':lambda x:x.id
            } if 'ulst' in locals() else {}

            acls = get_acls_on_object (sess, obj,**kw) # acl_users = ulst
            pprint.pprint (acls)
            print ('--- user output ---',)
            pprint.pprint(ulst)
            break
        else :
            print('no {} found...'.format(tp),file=sys.stderr)

if __name__ == '__main__':

    s = get_session()
    main(s,*sys.argv[2:])

