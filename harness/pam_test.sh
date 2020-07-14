#!/bin/bash

tabbed_output() {
  echo "$1"|sed $'s/^/\t\t/'
  echo $'\n'
}

TOTAL=0
PASSED=0

for opts in \
            " --pam_auth   --arg  --ssl=yes "\
            " --pam_auth   --arg  --ssl=no  "\
            " --irods_auth --env  --ssl=yes "\
            " --irods_auth --env  --ssl=no  "\
            " --irods_auth --arg  --ssl=yes "\
            " --irods_auth --arg  --ssl=no  "\
            " --pam_auth   --env  --ssl=yes "\
            " --pam_auth   --env  --ssl=no  "\
;do
  python -c "if True:
	from irods.connection import Connection
	exit(0 if getattr(Connection,'DISALLOWING_PAM_PLAINTEXT',
            	None) is not None else 1)" && \
  [[ $opts =~ --pam_auth ]] && \
  [[ $opts =~ --arg      ]] && \
  [[ $opts =~ --ssl=no   ]] && { continue; }
  ((TOTAL++))
  echo '[' $opts ']'
  x=$( 
       		python $(dirname $0)/irods_auth.py $opts -V3
  ) && ((PASSED++))
  y=$(tabbed_output "$x")
  printf '%s\n' "$y"
done

echo "------------------------------------"
echo "${PASSED} tests out of ${TOTAL} passed"
