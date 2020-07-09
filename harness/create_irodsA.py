import tempfile
import subprocess
import getpass

def create_auth_file(pw):
  p = None
  with tempfile.SpooledTemporaryFile() as f:
    f.write(pw + '\n')
    f.seek(0)
    f.read()
    f.seek(0)
    null=open('/dev/null','w')
    p = subprocess.Popen('iinit',stdout=null,stderr=null,stdin=f)
    p.communicate()
  return (p.returncode if p else None)

if __name__ == '__main__':
  s = getpass.getpass('enter (iRODS/PAM) password ->')
  print create_auth_file (s)
