import json
import atexit
import os
import ssl
import irods.exception
import unittest
import time
import socket
import pprint
from socket import gethostname
from irods.session import iRODSSession



ses = iRODSSession( 
        host=gethostname(),
	user='alissa',
	zone='tempZone',
	authentication_scheme='pam',
	password='test123',
	port= 1247
)
coll_name = '/{ses.zone}/home/{ses.username}'.format(**locals())
homecol = ses.collections.get(coll_name)
print homecol

