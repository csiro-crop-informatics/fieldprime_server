#!/bin/bash
 
EXPECTED_ARGS=2
E_BADARGS=65
MYSQL=`which mysql`
 
 
if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: $0 name password (and you will need Superadm password)"
  exit $E_BADARGS
fi

WEBUSER=fpwserver
DBNAME=fp_$1
DBUSER=fp_$1
DBPASS=$2 


$MYSQL -uSuperadm -p <<EOF
create database if not exists $DBNAME;
use $DBNAME;
source fprime.create.tables.sql;
grant all on $DBNAME.* to '$DBUSER'@'localhost' identified by '$DBPASS';
grant all on $DBNAME.* to '$WEBUSER'@'localhost';
flush privileges;
EOF

