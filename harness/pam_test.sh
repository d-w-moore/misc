#!/bin/bash

tabbed_output() {
  echo "$1"|sed $'s/^/\t\t/'
  echo $'\n'
}

for opts in \
            " -p -a -s. "\
            " -p -a "\
            " -i -ed "\
            " -i -a "\
            " -i -a -s. "\
            " -p -ed "\
;do
  echo '[' $opts ']'
  x=$( 
       		python $(dirname $0)/irods_auth.py $opts -V3
  ) 
  y=$(tabbed_output "$x")
  printf '%s\n' "$y"
done
