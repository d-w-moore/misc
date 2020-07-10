#!/bin/bash

tabbed_output() {
  echo "$1"|sed $'s/^/\t\t/'
  echo $'\n'
}

TOTAL=0
PASSED=0

for opts in \
            " -p -a -s.  "\
            " -p -a      "\
            " -i -ed     "\
            " -i -ed -s- "\
            " -i -a      "\
            " -i -a -s.  "\
            " -p -ed     "\
            " -p -ed -s- "\
;do
  (( TOTAL ++ ))
  echo '[' $opts ']'
  x=$( 
       		python $(dirname $0)/irods_auth.py $opts -V3
  ) && (( PASS++ ))
  y=$(tabbed_output "$x")
  printf '%s\n' "$y"
done

echo "------------------------------------"
echo "${PASS} tests out of ${TOTAL} passed"
