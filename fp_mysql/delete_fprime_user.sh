#!/bin/bash
 
EXPECTED_ARGS=1
E_BADARGS=65
MYSQL=`which mysql`
 
 
if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: $0 name (and you will need Superadm password)"
  exit $E_BADARGS
fi

PROJNAME=$1
DBNAME=fp_$PROJNAME
DBUSER=fp_$PROJNAME


$MYSQL -uSuperadm -p <<EOF
drop database $DBNAME;
drop user '$DBUSER'@'localhost';
delete from fpsys.project where name = '$PROJNAME'
EOF

