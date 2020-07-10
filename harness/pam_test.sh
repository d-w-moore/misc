#!/bin/bash

tabbed_output() {
  echo "$1"|sed $'s/^/\t\t/'
  echo $'\n'
}

TOTAL=0
PASSED=0

for opts in \
            " --pam   --arg  --ssl=yes "\
            " --pam   --arg            "\
            " --irods --env            "\
            " --irods --env  --ssl=no  "\
            " --irods --arg            "\
            " --irods --arg  --ssl=yes "\
            " --pam   --env            "\
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
