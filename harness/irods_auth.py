#!/usr/bin/env python

from __future__ import print_function
import os, ssl, sys, getopt, socket
from shutil import copytree, rmtree
from os.path import exists, isdir, isfile, islink, expanduser, abspath, dirname,join
from irods.session import iRODSSession

# ________ manual tests __________

# aa) native with password in session()
# bb) pam with password in session()
# cc) native with .irodsA
# dd) pam with .irodsA
# ee) native with password in irods_environment.json
# ff) pam with password in irods_environment.json

# _____________ results __________

# - - with patch

# aa)
# bb)
# cc) 
# dd)
# ee) 
# ff)

# - - without patch

# aa)
# bb)
# cc) 
# dd)
# ee) 
# ff)

# Notes
#  1. needed: handle DONT_CARE on client side


ENV_DIR = None
VERBOSE = False
EXIT = False
pw_opt = ''

class UnrecognizedFileTypeError(RuntimeError): pass
class CouldNotDeleteError(RuntimeError): pass

##############################################
# This script deletes current .irods directory
##############################################

def remove_dot_irods ( path_ = None):

  if path_ is None:
    path_ = expanduser(  '~/.irods')
  else:
    path_ = abspath( path_ )

  if not exists (path_):
    return

  if islink(path_) or isfile(path_):
    os.unlink(path_)
  elif isdir(path_):
    rmtree(path_)
  else:
    raise UnrecognizedFileTypeError

  if exists( path_ ): raise CouldNotDeleteError

SCRIPTDIR = dirname(sys.argv[0])


def create_dircopy ( auth ):

  COPY_TO_NAME = expanduser(  '~/.irods')
  COPY_FM_NAME = abspath(join( SCRIPTDIR,'irods-{}'.format( auth.upper())))
  remove_dot_irods(COPY_TO_NAME)
  if ENV_DIR:
    copytree(COPY_FM_NAME,COPY_TO_NAME)

    
def create_symlink ( auth ):

  LINK_NAME = expanduser(  '~/.irods')
  DST_NAME = abspath(join( SCRIPTDIR,'irods-{}'.format( auth.upper())))

  if exists(LINK_NAME) :
    remove_dot_irods(LINK_NAME)

  if ENV_DIR:
    os.symlink (DST_NAME,LINK_NAME)

    if VERBOSE:
      linked_ = os.readlink (LINK_NAME)
      print( "DEBUG -> {LINK_NAME} pointing at  {linked_}".format(**locals()) , file = sys.stderr)

#############################################

try:
  opt,arg = getopt.getopt(sys.argv[1:], 'h:s:e:alxv''pi''P:', ['password='])
except getopt.GetoptError as e:
  print ( """\n\
  Usage: {} [-lvxipea] [ -s <crtpath> ] [ --password <pwd> ]  ...options
      		-x	exit after symlinking/copying auth dir
      		-v	verbose
      		-s	add SSL opts to cmd line
      		-h	hostname
      		--password=<password>

        options (___Auth category___):	-i	AUTH with irods     
					-p	AUTH with pam
     	options (___Call style___):	-e <L|D>	load environment file from (Link/Directory)
					-a	pass args for Authentication
    \n""".format(sys.argv[0])
  )
  sys.exit(126)

pw = { None: None, 
       'irods' :  'apass',
       'pam'   :  'test123' }

Host = socket.gethostname()
AUTH = None  #  None, 'irods', 'pam'
METHOD = 'env'  # args , env
SSL_cert = False

for key,val in opt:
  if  key == '--password' : pw_opt = val
  if  key == '-p' : AUTH = 'pam'
  if  key == '-i' : AUTH = 'irods'
  if  key == '-a' : METHOD = 'args'
  if  key == '-e' : METHOD = 'env' ;\
                    ENV_DIR = val.lower()
  if  key == '-s' : SSL_cert = val
  if  key == '-v' : VERBOSE = True
  if  key == '-x' : EXIT = True
  if  key == '-d' : ENV_DIR = 'copy'
  if  key == '-l' : ENV_DIR = 'link'
  if  key == '-h' : Host = val

if SSL_cert and ('/' not in SSL_cert): SSL_cert ='/etc/irods/ssl/irods.crt'

SSL_Options = {
    "irods_client_server_negotiation": "request_server_negotiation",
    "irods_client_server_policy": "CS_NEG_REQUIRE",
    "irods_ssl_verify_server": "cert",
    "irods_encryption_key_size": 16,
    "irods_encryption_salt_size": 8,
    "irods_encryption_num_hash_rounds": 16,
    "irods_encryption_algorithm": "AES-256-CBC",
}

#=================================

def main():

  if AUTH is not None and ENV_DIR:
    (create_symlink if ENV_DIR == 'l' else create_dircopy) (AUTH)
  if EXIT: return 0

  settings = {}

  if AUTH == 'pam': 
    settings.update ( authentication_scheme = 'pam')

  if METHOD == 'env':
    settings [ 'irods_env_file' ] = os.path.expanduser ('~/.irods/irods_environment.json') 

  else:

    settings.update ( host=Host,
                      port=1247,
                      user='alissa', 
                      zone='tempZone',
                      password=(pw_opt if pw[AUTH] is None else pw[AUTH]))

  if SSL_cert:

    ssl_context = ssl.create_default_context ( purpose=ssl.Purpose.SERVER_AUTH,
                                               capath=None,
                                               cadata=None,
                                               cafile = SSL_cert )

    if METHOD == 'args': settings.update( SSL_Options )

### y = ssl_context.load_verify_locations(cafile=SSL_cert)
    settings [ 'ssl_context' ] = ssl_context


  if VERBOSE: _ = "\n".join( "{0:<10} : {{""{0}""}}".format(x) for x in ("SSL_cert","METHOD","AUTH"))+"\n";\
              print (_.format(**dict(globals().items()+locals().items())) , file = sys.stderr)
  
  with iRODSSession( ** settings ) as session:
    c = session.collections.get('/tempZone/home/alissa')
    if VERBOSE : print ( c.data_objects, file = sys.stderr )

  return 0

#=================================

if __name__ == '__main__': 

  retvalue = main ()

  if VERBOSE: print ( '***********\n',
                      'retvalue = ',retvalue,
                    '\n***********\n', file = sys.stderr)

  sys.exit(retvalue)
