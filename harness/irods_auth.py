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

def usage():

  print ( """
  Usage: {} [-lvxipa] [ -s <crtpath> ] ... options:

      (preferred) long options:

      		--ssh_option={{ yes | no | "/path/to/cert" }}

		Auth Type:
      			--irods_auth
      			--pam_auth

                Method to supply constructor for iRODSSession
                	--env_dir
                	--args

      		--password={{ password }}

      (low-level) short options:

		-k	skip deletion/creation of auth dir ( same as -K1 )
                -K n where n =
                    0 ultimate freedom                           H  O
                    1 change hostname, and only if incorrect     H  -
                    2 change nothing                             -  -
      		-x	exit after symlinking/copying auth dir
      		-v	stderr verbose on
      		-V N	stdout verbose on, level N
      		-s	add SSL opts to cmd line
      		-h	hostname
      		-E	show Exception detail

        options (___Auth category___):	-i	AUTH with irods
					-p	AUTH with pam
     	options (___Call style___):	-e <L|D>	load environment file from (Link/Directory)
					-a	pass args for Authentication
    \n""".format(sys.argv[0])
  )
  sys.exit(125)


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
# aa-s)   ( -i  -a -s. )
# bb)     ( -p  -a  )      YES     --> with and w/o "s." bb-s)
# cc)     ( -i  -ed )      YES
# cc-s)   ( -i  -ed -s. )
# dd)     ( -p  -ed )      YES     --> with and w/o "s." dd-s)
# ee) ---
# ff) ---

# - - without patch

# aa)
# bb)
# cc)
# dd)
# ee) ---
# ff) ---

DEFAULT_CERT_PATH = '/etc/irods/ssl/irods.crt'
ENV_DIR_PATH = expanduser( '~/.irods' )
ENV_DIR_FILE_PATH = path_join( ENV_DIR_PATH, 'irods_environment.json' )
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
class BadCertificatePath(RuntimeError):        code = 114

def ls_environment_dir( ):
  try:
    return os.listdir(ENV_DIR_PATH)
  except OSError as e:
    if e.errno == ENOENT:  return None
    else: raise
  return list()

def save_environment(j):
  with open( ENV_DIR_FILE_PATH,'w' ) as f:
    json.dump(j,f,indent=4)

def load_environment():
  try:
    with open(ENV_DIR_FILE_PATH,'r') as f:
      return json.load(f)
  except: pass

def delete_keys_in_dict ( D, key_condition ):
  keys = D.keys()
  for k in keys:
    if key_condition(k): del D[k]

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

SKIP_AUTH_DIR_MANIP = 0

try:
  opt,arg = getopt.getopt(sys.argv[1:], 'kK:h:s:e:alxvV:E''pi''P:', [
                          'password=',
                          'irods_auth',
                          'pam_auth',
                          'env_dir',
                          'args',
                          'help',
                          'ssl_option=',
                          ])
except getopt.GetoptError as e:
  usage()

pw = { None: None,
       'irods' :  'apass',
       'pam'   :  'test123' }

SSL_Options = {
    "irods_client_server_negotiation": "request_server_negotiation",
    "irods_client_server_policy": "CS_NEG_REQUIRE",
    "irods_ssl_verify_server": "cert",
    "irods_encryption_key_size": 16,
    "irods_encryption_salt_size": 8,
    "irods_encryption_num_hash_rounds": 16,
    "irods_encryption_algorithm": "AES-256-CBC",
}

Host = socket.gethostname()
AUTH = None  #  None, 'irods', 'pam'
METHOD = 'env'  # args , env
SSL_cert = False

for key,val in opt:
  #
  # -- short options
  #
  if  key == '--help' : usage()
  elif  key == '--password' : pw_opt = val
  elif  key == '-p' : AUTH = 'pam'
  elif  key == '-i' : AUTH = 'irods'
  elif  key == '-a' : METHOD = 'args'
  elif  key == '-e' :
    METHOD = 'env'
    ENV_DIR = val.lower()
    if 'dl'.find(ENV_DIR) < 0: raise Bad_Env_Dir_Opt ("need -e arg to be 'l' or 'd'")
  elif  key == '-s' : SSL_cert = val
  elif  key == '-v' : ErrVerbose = True;
  elif  key == '-V' : OutVerbose = int(val)
  elif  key == '-x' : EXIT = True
  elif  key == '-h' : Host = val
  elif  key == '-E' : show_Exception = True
  elif  key == '-k' : SKIP_AUTH_DIR_MANIP = 1
  elif  key == '-K' : SKIP_AUTH_DIR_MANIP = int(val)
  #
  # -- long options
  #
  elif  key .startswith('--'):
      if   key.endswith('-pam_auth'):    AUTH = 'pam'
      elif key.endswith('-irods_auth'):  AUTH = 'irods'
      elif key.endswith('-ssl'):
          if SSL_cert[:1] in "ynYN":  # yes will use DEFAULT_CERT_PATH
              # translate to short option value : "." default cert path , "-" no use of SSL
              SSL_cert = { "Y":".", "N":"-" }[val.upper()]
          else: # override cert path
              SSL_cert = val
              if "/" not in SSL_cert: raise BadCertificatePath
      elif key.endswith('-args'):      METHOD = 'args'
      elif key.endswith('-env_dir'):     
          METHOD = 'env'
          ENV_DIR = 'd'

if SKIP_AUTH_DIR_MANIP not in (0,1,2):
  raise ValueError ('"-k/-K" option value out of range');

suppress_env_ssl = False

if SSL_cert:

  if SSL_cert == '-' and METHOD == 'env':

    suppress_env_ssl = True
    SSL_cert = False

  elif SSL_cert not in ('','-') and ('/' not in SSL_cert):

    SSL_cert = DEFAULT_CERT_PATH

#=================================


def main():

  global SSL_cert
  exitcode = 100
  try:

    error = False

    if (SKIP_AUTH_DIR_MANIP==0) :
      remove_dot_irods(ENV_DIR_PATH)
      if AUTH is not None and ENV_DIR:
        error = not(
          (create_symlink if ENV_DIR == 'l' else create_dircopy) (AUTH)
        )
    if EXIT:  return 126
    if error: return 127

    settings = {}

    password_ = (pw_opt if pw[AUTH] is None else pw[AUTH])

    env_json = load_environment()

    #----------------------
    if env_json is not None:
      host_setting = env_json ['irods_host']
      if (host_setting != Host) and (SKIP_AUTH_DIR_MANIP in (0,1)) :
        env_json ['irods_host'] = Host
        if SKIP_AUTH_DIR_MANIP != 0: print("WARNING, correcting host setting in env", file=sys.stderr)
        save_environment (env_json)

    if (SKIP_AUTH_DIR_MANIP==0):
      if ENV_DIR == 'd' and password_ :
        create_auth_file ( password_ )

    if env_json:
      if suppress_env_ssl and (SKIP_AUTH_DIR_MANIP==0):
        delete_keys_in_dict( env_json, lambda k : k.startswith('irods_ssl_')    or        \
                                                  k.startswith('irods_encryption_') or    \
                                                  k in ( 'irods_client_server_policy',
                                                         'irods_client_server_negotiation') )
        save_environment (env_json)
    #----------------------

    if METHOD == 'env':

      env_filename = settings [ 'irods_env_file' ] = ENV_DIR_FILE_PATH
      env_json = json.load( open( env_filename) )
      SSL_cert = env_json.get('irods_ssl_ca_certificate_file', None)

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
        print( "env / auth files dir list: " + str(ls_environment_dir()))
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

