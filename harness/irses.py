import json
import atexit
import os
import ssl
import irods.exception
import unittest
import time
import socket
import pprint

from irods.session import iRODSSession

def default_session_args_inline(password_):
  args = dict(
    host=socket.gethostname(),
    port=1247,
    user='alissa',
    zone='tempZone',
    password= password_
  )
  return args

session = None

pw = 'apass'

def get_session( hint = None ):

    global session

    if session is None:

            try:
                env_file = os.environ['IRODS_ENVIRONMENT_FILE']
            except KeyError:
                env_file = os.path.expanduser('~/.irods/irods_environment.json')

            irods_env = json.load (open(env_file))

            ssl_context = None
            ssl_settings = {}

            ssl_context = ssl.create_default_context( purpose=ssl.Purpose.SERVER_AUTH,
                                                      cafile=irods_env['irods_ssl_ca_certificate_file'], 
                                                      capath=None,
                                                      cadata=None)

#           if 'irods_ssl_ca_certificate_file' in irods_env:
#                     ssl_context.load_verify_locations(cafile=irods_env['irods_ssl_ca_certificate_file'])

            ssl_settings = {'ssl_context': ssl_context}

            session = iRODSSession( irods_env_file = env_file
                                      ,** ssl_settings
            )

            atexit.register(lambda : session.cleanup() if session else None)
    return session

if __name__ == '__main__':

    import pprint
    ses = get_session()
    coll_name = '/{ses.zone}/home/{ses.username}'.format(**locals())
    homecol = ses.collections.get(coll_name)
    print homecol

