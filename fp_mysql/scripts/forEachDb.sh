#!/bin/bash
#
# Retrieves the list of names of  fp_* databases, and then calls
# specified command for each one (with variable $DBNAME set to the
# database name).  The command can be mysql, from the command line
# or a file, or a bash command from the command line.
# The variable $DBPW will be also set to the password entered (so you
# don't have to reenter the password for each database).
#
# EG:
# ./forEachDb.sh -b 'echo $DBNAME'     # Note single quotes else use \$DBNAME
# ./forEachDb.sh -e 'select count(*) as numTrials from trial'
# ./forEachDb.sh -f mySqlScript.sql
# ./forEachDb.sh -b 'mysqldump -uSuperadm -p$DBPW $DBNAME > $DBNAME.sql'
# 
# 
#

usageText="
Usage: $0 -e <mysql command string> | -f <mysql command file> | -b <bash command>

Calls the specified command for each FieldPrime database (i.e. those
named fp_*) in the local mysql server. For each call the variable \$DBNAME
is set to the database name.
The command can be mysql - from the command line or a file - or a bash command.

You will be prompted for the mysql password for the Superadm user.

The variable \$DBPW will be also set to the password entered (so you
don't have to reenter the password for each database).

Examples:
---------
List the database names:
$0 -b 'echo \$DBNAME'     # Note single quotes else use \\\$DBNAME

Count the trials in each database:
$0 -e 'select count(*) as numTrials from trial'

Run an sql script on each database (eg to add a column to some table):
$0 -f mySqlScript.sql

Backup each database with mysqldump:
  $0 -b 'mysqldump -uSuperadm -p\$DBPW \$DBNAME > \$DBNAME.sql'
"

usage() {
  echo "$usageText" 1>&2
#  echo "Usage: $0 -e <mysql command string> | -f <mysql command file> | -b <bash command>" 1>&2
#  echo "  (and you will need Superadm password)" 1>&2
  exit 1;
}

numOpt=0
while getopts "f:e:b:h" o; do
    case "${o}" in
        f)
            INFILE=${OPTARG}
            ((numOpt++))
            ;;
        e)
            CMD=${OPTARG}
            #printf "cmd: %s\n" "$CMD"
            ((numOpt++))
           ;;
        b)
            BCMD=${OPTARG}
            ((numOpt++))
            ;;
        h)
            usage
            ;;
        *)
            usage
            ;;
    esac
done
if [ $numOpt -ne 1 ]; then
  echo "Wrong number of parameters"
  usage
fi


echo "Please enter password"
read -s DBPW
MYSQL=`which mysql` 
DATABASES=`mysql -BN  -uSuperadm -p$DBPW -e"show databases"`
for DBNAME in $DATABASES; do if [[ $DBNAME == fp_* ]];
then
  echo Processing $DBNAME:
  if [ -n "$CMD" ]; then
    export MCMD="$MYSQL -uSuperadm -p$DBPW $DBNAME -e \"$CMD\""
  elif [ -n "$INFILE" ]
  then
    export MCMD="$MYSQL -uSuperadm -p$DBPW $DBNAME  < $INFILE"
  else
    export MCMD=$BCMD
  fi
  eval "$MCMD"   # quotes needed else shell can interpret things in command
fi
done


