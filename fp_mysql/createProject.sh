#!/bin/bash
 
EXPECTED_ARGS=3
E_BADARGS=65
MYSQL=`which mysql`
 
#echo numargs $#
# Show usage if wrong number of args: 
if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: $0 projectName contactName contactEmail"
  echo "  You will need to provide mysql super password."
  exit $E_BADARGS
fi

WEBUSER=fpwserver
PROJNAME=$1
DBNAME=fp_$PROJNAME
CONTACT_NAME=$2
CONTACT_EMAIL=$3

#echo projname $PROJNAME
#echo name $CONTACT_NAME
#echo email $CONTACT_EMAIL
#exit 0

# Run Mysql script:
$MYSQL -uSuperadm -p <<EOF
create database if not exists $DBNAME;
use $DBNAME;
source fprime.create.tables.sql;
grant all on $DBNAME.* to '$WEBUSER'@'localhost';
insert fpsys.project (name, dbname) values ('$PROJNAME', '$DBNAME');
insert project (id, up_id, name, contactName, contactEmail) values ((select id from fpsys.project where name='$PROJNAME'), null, '$PROJNAME', '$CONTACT_NAME', '$CONTACT_EMAIL');
flush privileges;
insert system (name, value) values ('contactName', '$CONTACT_NAME'), ('contactEmail', '$CONTACT_EMAIL');
EOF

