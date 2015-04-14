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
PROJNAME=$1
DBNAME=fp_$PROJNAME
DBUSER=fp_$PROJNAME
DBPASS=$2 
CONTACT_NAME=$3
CONTACT_EMAIL=$4


$MYSQL -uSuperadm -p <<EOF
create database if not exists $DBNAME;
use $DBNAME;
source fprime.create.tables.sql;
grant all on $DBNAME.* to '$DBUSER'@'localhost' identified by '$DBPASS';
grant all on $DBNAME.* to '$WEBUSER'@'localhost';
insert project values (2, null, '$PROJNAME', '$CONTACT_NAME', 'CONTACT_EMAIL');
insert fpsys.project values (null, '$PROJNAME', '$DBNAME');
flush privileges;
insert system (name, value) values ('contactName', '$CONTACT_NAME'), ('contactEmail', '$CONTACT_EMAIL')
EOF

