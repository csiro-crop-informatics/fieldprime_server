#!/bin/bash
 
EXPECTED_ARGS=1
E_BADARGS=65
MYSQL=`which mysql` 

if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: $0 <mysql command string> (and you will need Superadm password)"
  exit $E_BADARGS
fi
CMD=$1

echo "Please enter password"
read -s DBPW

DATABASES=`mysql -BN  -uSuperadm -p$DBPW -e"show databases"`
for DBNAME in $DATABASES; do if [[ $DBNAME == fp_* ]];
then
export MCMD="$MYSQL -uSuperadm -p$DBPW $DBNAME -e \"$CMD\""
eval $MCMD
fi
done


