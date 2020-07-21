# running this test harness 

  * evaluates Python iRODS Client authentication suite in all sensible  combinations of
    - iRODS and PAM  authentication
    - SSL and no SSL
    - use of
      1. environment directory and files, or 
      1. arguments given to iRODSSession

## Procedure

checkout PRC from this fork :
```
  git clone https://github.com/gscteam/python-irodsclient
```
  - Apply this [patch](https://github.com/irods/python-irodsclient/pull/191/commits/888be407ceab6bb69073644aec88439d6199feed) on top of
    10 July 2020 current master [tip](https://github.com/irods/python-irodsclient/tree/423cef2319bddc9fca019bb91c09e22316e58508)
  - As system admin ,create Unix user alissa with login password 'test123'
  - cd into the python-irodsclient directory and do: `pip install -e .`
  - With iRODS 4.2.8 installed and the server configured for SSL (per [these slides](http://slides.com/irods/ugm2018-ssl-and-pam-configuration))
  - Change core.re setting to CS_NEG_REQUIRE
  - With the extra SSL settings added per above slides in ~irods/.irods/irods_environment.json, verify you can ils as irods service account
  - Create user alissa login with unix login 'test123' and irods password 'apass'
  - Change core.re setting back to default, CS_NEG_DONT_CARE.
  - make a test dir as user alissa and clone this repo under it
  ```
  mkdir ~/test; cd ~/test; git clone -b prc_pam_test http://github.com/d-w-moore/misc
  ```
  - run the tests
  ```
  localhost:~/test $ ./misc/harness/pam_test.sh 2>&1  |tee test_results_without_patch
  ```
  the last two will fail without the patch (so 6/8 test pass in total)
  when applying the above gscteam patch for pam w/ env file (since we used pip with -e , just check out that SHA from the local repo and re-run the script to
  observer the full 8 of 8 tests passing)


