#!/bin/bash

tabbed_output() {
  echo "$1"|sed $'s/^/\t\t/'
  echo $'\n'
}

TOTAL=0
PASSED=0

for opts in \
            " --pam   --arg  --ssl=yes "\
            " --pam   --arg  --ssl=no  "\
            " --irods --env  --ssl=yes "\
            " --irods --env  --ssl=no  "\
            " --irods --arg  --ssl=yes "\
            " --irods --arg  --ssl=no  "\
            " --pam   --env  --ssl=yes "\
            " --pam   --env  --ssl=no  "\
;do
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
