#!/usr/bin/env python

from __future__ import print_function
import os, ssl, sys, getopt, socket, subprocess, tempfile, json
from shutil import copytree, rmtree
from os.path import ( exists, isdir, isfile, islink, expanduser, dirname,
                      abspath, realpath, join as path_join )
from irods.session import iRODSSession
from irods.collection import iRODSCollection
from errno import ENOENT

from irods.connection import Connection

Connection._login_pam_2 = Connection._login_pam
def verbose_login_pam(self):
  print('calling PAM login')
  self._login_pam_2()
setattr( Connection, '_login_pam', verbose_login_pam)

SCRIPTDIR = dirname(realpath(sys.argv[0]))
sys.path.insert(0,SCRIPTDIR)
from create_irodsA import create_auth_file  # --> for creating ~/.irods/.irodsA

# ________ manual tests __________ (run with server setting CS_NEG_DONT_CARE)
#   -ed : copies from realpath(sys.argv[0]/irods.AUTHMETHOD; calls iinit to make a new AUTH file) 
#   -a  : calls the iRODSSession constructor using no env_file.
#         (WARNING when running this test script. '-a' without '-k' recursively deletes ~/.irods)
#   -s arg: use SSL. arg is abs path to certificate file; '.' defaults to /etc/irods/ssl/irods.crt
#   -i irods password auth
#   -i pam password auth

# aa) native with password in session()			( -i  -a  )                     YES
# bb) pam with password in session()			( -p  -a  )                     YES
# cc) native with .irodsA				( -i  -ed )                     YES
# dd) pam with .irodsA					( -p  -ed )                     NO
# ee) native with password in irods_environment.json  (----------------- n/a )
# ff) pam with password in irods_environment.json     (----------------- n/a )

# _____________ results __________

# - - with patch

# aa)     ( -i  -a  )      YES
# bb)     ( -p  -a  )      YES
# cc)     ( -i  -ed )      YES
# dd)     ( -p  -ed )      YES
# ee) ---
# ff) ---

# - - without patch

# aa)
# bb)
# cc) 
# dd)
# ee) ---
# ff) ---

ENV_DIR_PATH = expanduser( '~/.irods' )
ENV_DIR = None
ErrVerbose =  False
OutVerbose =  1
EXIT = False
pw_opt = ''
show_Exception = False

class UnrecognizedFileTypeError(RuntimeError): code = 110
class CouldNotDeleteError(RuntimeError):       code = 111
class CouldNotCreateError(RuntimeError):       code = 112
class LogicError(RuntimeError):                code = 113

def ls_environment( ):
  try:
    return os.listdir(ENV_DIR_PATH)
  except OSError as e:
    if e.errno == ENOENT:  return None
    else: raise
  return list()

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

def create_dircopy ( auth ):
  COPY_TO_NAME = ENV_DIR_PATH
  if exists(COPY_TO_NAME) : raise CouldNotDeleteError
  COPY_FM_NAME = abspath(path_join( SCRIPTDIR,'irods-{}'.format( auth.upper())))
  if ENV_DIR:
    copytree(COPY_FM_NAME,COPY_TO_NAME)
    if not exists(COPY_TO_NAME) : return False
  return True
    
def create_symlink ( auth ):
  LINK_NAME = ENV_DIR_PATH
  if exists(LINK_NAME) : raise CouldNotDeleteError
  DST_NAME = abspath(path_join( SCRIPTDIR,'irods-{}'.format( auth.upper())))
  if ENV_DIR:
    os.symlink (DST_NAME,LINK_NAME)
    if not exists(LINK_NAME) : return False
    if ErrVerbose:
      linked_ = os.readlink (LINK_NAME)
      print( "DEBUG -> {LINK_NAME} pointing at  {linked_}".format(**locals()) , file = sys.stderr)
  return True

#############################################

class Bad_Env_Dir_Opt (RuntimeError): pass

SKIP_AUTH_DIR_MANIP = False

try:
  opt,arg = getopt.getopt(sys.argv[1:], 'kh:s:e:alxvV:E''pi''P:', ['password='])
except getopt.GetoptError as e:
  print ( """\n\
  Usage: {} [-lvxipa] [ -s <crtpath> ] [ --password <pwd> ]  ...options
      		-k	skip deletion/creation of auth dir
      		-x	exit after symlinking/copying auth dir
      		-v	stderr verbose on
      		-V N	stdout verbose on, level N
      		-s	add SSL opts to cmd line
      		-h	hostname
      		-E	show Exception detail
      		--password=<password>

        options (___Auth category___):	-i	AUTH with irods     
					-p	AUTH with pam
     	options (___Call style___):	-e <L|D>	load environment file from (Link/Directory)
					-a	pass args for Authentication
    \n""".format(sys.argv[0])
  )
  sys.exit(125)

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
  if  key == '-e' :
    METHOD = 'env'
    ENV_DIR = val.lower()
    if 'dl'.find(ENV_DIR) < 0: raise Bad_Env_Dir_Opt ("need -e arg to be 'l' or 'd'")
  if  key == '-s' : SSL_cert = val
  if  key == '-v' : ErrVerbose = True;
  if  key == '-V' : OutVerbose = int(val)
  if  key == '-x' : EXIT = True
  if  key == '-h' : Host = val
  if  key == '-E' : show_Exception = True
  if  key == '-k' : SKIP_AUTH_DIR_MANIP = True

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

  global SSL_cert
  exitcode = 100
  try:

    error = False

    if not SKIP_AUTH_DIR_MANIP :
      remove_dot_irods(ENV_DIR_PATH)
      if AUTH is not None and ENV_DIR:
        error = not(
          (create_symlink if ENV_DIR == 'l' else create_dircopy) (AUTH)
        )
    if EXIT:  return 126
    if error: return 127

    settings = {}

    password_ = (pw_opt if pw[AUTH] is None else pw[AUTH])

    if not SKIP_AUTH_DIR_MANIP :
      if  ENV_DIR == 'd' and password_ :
        create_auth_file ( password_ )

    if METHOD == 'env':

      env_filename = settings [ 'irods_env_file' ] = path_join (ENV_DIR_PATH, 'irods_environment.json') 
      env_json = json.load( open( env_filename) )
      SSL_cert = env_json .get('irods_ssl_ca_certificate_file', None)

    else:

      if not password_ : raise LogicError ('No password when using Args method of session init')

      settings.update ( host=Host,
                        port=1247,
                        user='alissa', 
                        zone='tempZone',
                        password=password_ )

    if SSL_cert:

      ssl_context = ssl.create_default_context ( purpose=ssl.Purpose.SERVER_AUTH,
                                                 capath=None,
                                                 cadata=None,
                                                 cafile = SSL_cert )
      settings [ 'ssl_context' ] = ssl_context

    if METHOD == 'args':
      if AUTH == 'pam' : settings.update ( authentication_scheme = 'pam')
      if SSL_cert:       settings.update(  SSL_Options )

    if ErrVerbose:
      _ = "\n".join( "{0:<10} : {{""{0}""}}".format(x) for x in ("SSL_cert","METHOD","AUTH"))+"\n"
      print (_.format(**dict(globals().items()+locals().items())) , file = sys.stderr)
  
    with iRODSSession( **settings ) as session:

      home_coll = '/{0.zone}/home/{0.username}'.format(session)
      c = session.collections.get(home_coll)

      if OutVerbose >= 2:
        my_connect = [s for s in (session.pool.active|session.pool.idle)] [0]
        print ('auth_scheme = {}'.format(my_connect.account.authentication_scheme))
        print ('socket = {}'.format(my_connect.socket.__class__))

      if OutVerbose >= 3:
        print( "env / auth files dir list: " + str(ls_environment()))
        print( "Home Collection = '{0.path}/{0.name}' ".format(c))
        print ( "With data objects: {!r}".format(c.data_objects))

      exitcode = (0 if type(c) is iRODSCollection else 1)

  except Exception as e:
    if show_Exception: raise
    print ( '--->',repr(e), file = sys.stderr)
    exitcode = int(getattr(e, 'code', '0')) or 100

  if OutVerbose >= 1: print ('Exiting with code',exitcode)
  exit (exitcode)

#=================================

if __name__ == '__main__': 

  retvalue = main ()

  sys.exit(retvalue) # 0       -> success 
                     # 1..N    -> failure
                     # 100,101 -> unexpected error

