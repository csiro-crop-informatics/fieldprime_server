#!/bin/bash
 
EXPECTED_ARGS=4
E_BADARGS=65
MYSQL=`which mysql`
 
 
if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: $0 name password contactName contactEmail"
  echo "  You will need super password."
  exit $E_BADARGS
fi

WEBUSER=fpwserver
DBNAME=fp_$1
DBUSER=fp_$1
DBPASS=$2 
CONTACT_NAME=$3
CONTACT_EMAIL=$4


$MYSQL -uSuperadm -p <<EOF
create database if not exists $DBNAME;
use $DBNAME;
source fprime.create.tables.sql;
grant all on $DBNAME.* to '$DBUSER'@'localhost' identified by '$DBPASS';
grant all on $DBNAME.* to '$WEBUSER'@'localhost';
flush privileges;
insert system (name, value) values ('contactName', '$CONTACT_NAME'), ('contactEmail', '$CONTACT_EMAIL')
EOF

