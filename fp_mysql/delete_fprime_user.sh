#!/bin/bash
 
EXPECTED_ARGS=1
E_BADARGS=65
MYSQL=`which mysql`
 
 
if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: $0 name (and you will need Superadm password)"
  exit $E_BADARGS
fi

DBNAME=fp_$1
DBUSER=fp_$1


$MYSQL -uSuperadm -p <<EOF
drop database $DBNAME;
drop user '$DBUSER'@'localhost';
EOF

