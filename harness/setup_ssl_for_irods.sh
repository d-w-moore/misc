#!/bin/bash
mkdir -p /etc/irods/ssl && cd /etc/irods/ssl && {
    openssl genrsa -out irods.key 2048
    chmod 600 irods.key
    openssl req -new -x509 -key irods.key -out irods.crt -days 365 <<-EOF
	US
	North Carolina
	Chapel Hill
	UNC
	RENCI
	`hostname`
	anon@mail.com
	EOF
    openssl dhparam -2 -out dhparams.pem 
}  2>/dev/null 
