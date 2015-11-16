#!/bin/bash
 
EXPECTED_ARGS=3
E_BADARGS=65
MYSQL=`which mysql`
 
echo numargs $#

while getopts "p:" opt; do
case $opt in
    p)
      DBPASS=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done
shift $(expr $OPTIND - 1 )

echo numargs $#
echo optind $OPTIND 
echo difference $[$# - $OPTIND]

# Show usage if wrong number of args: 
if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: $0 name [-p password] projectName contactName contactEmail"
  echo "  You will need to provide mysql super password."
  echo '  If -p password is present, then a FieldPrime user is created (with that password).'
  exit $E_BADARGS
fi

WEBUSER=fpwserver
PROJNAME=${@:$OPTIND:1}
DBNAME=fp_$PROJNAME
DBUSER=fp_$PROJNAME
CONTACT_NAME=${@:$OPTIND+1:1}
CONTACT_EMAIL=${@:$OPTIND+2:1}

# Mysql command to create user if specified:
if [ -n ${DBPASS+x} ]
then
    CREATE_USER_CMD="grant all on $DBNAME.* to '$DBUSER'@'localhost' identified by '$DBPASS';"
fi

echo projname $PROJNAME
echo name $CONTACT_NAME
echo email $CONTACT_EMAIL
exit 0

# Run Mysql script:
$MYSQL -uSuperadm -p <<EOF
create database if not exists $DBNAME;
use $DBNAME;
source fprime.create.tables.sql;
# Create mysql user if password provided:
$CREATE_USER_CMD
grant all on $DBNAME.* to '$WEBUSER'@'localhost';
insert project values (2, null, '$PROJNAME', '$CONTACT_NAME', '$CONTACT_EMAIL');
insert fpsys.project values (null, '$PROJNAME', '$DBNAME');
flush privileges;
insert system (name, value) values ('contactName', '$CONTACT_NAME'), ('contactEmail', '$CONTACT_EMAIL')
EOF

