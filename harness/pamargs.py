import json
import atexit
import sys
import os
import ssl
import irods.exception
import unittest
import time
import socket
import pprint
from socket import gethostname
from irods.session import iRODSSession
import irods.password_obfuscation

import irods.connection
import  getopt

demo_user =  'alissa'
demo_passw = 'test123'


opt,arg = getopt.getopt( 
    sys.argv[1:], '', ['output=',
                       'environment-directory=']) 

env_dir = ('~/')
out_filename = ''

for key,val in opt:
    if key == '--output':		 out_filename = val
    if key == '--environment-directory': env_dir = val

env_dir = os.path.expanduser( env_dir )

#--------------

irods.connection.Connection.DISALLOWING_PAM_PLAINTEXT = False

ses = iRODSSession( 
        host=gethostname(),
	user='alissa',
	zone='tempZone',
	authentication_scheme='pam',
	password='test123',
	port= 1247
)

pam_hash = ses.pam_pw_negotiated

if pam_hash: 
    print (pam_hash[0])
    native_mode_encoded = irods.password_obfuscation.encode( pam_hash[0] )
    open(out_filename,'w').write(native_mode_encoded)

coll_name = '/{ses.zone}/home/{ses.username}'.format(**locals())
homecol = ses.collections.get(coll_name)
print ( homecol )

