#!/bin/bash
 
usage() {
  echo "Usage: $0 -e <mysql command string> | -f <mysql command file>" 1>&2
  echo "  (and you will need Superadm password)" 1>&2
  exit 1;
}

if [ -n "$CMD" ] && [ -n "$INFILE" ]; then
  echo "jjjjjToo many parameters"
  usage
fi

while getopts "f:e:" o; do
    case "${o}" in
        f)
            INFILE=${OPTARG}
            ;;
        e)
            CMD=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

if [ -n "$CMD" ] && [ -n "$INFILE" ]; then
  echo "Too many parameters"
  usage
fi
if [ -z "$CMD" ] && [ -z "$INFILE" ]; then
  echo "Not enough parameters"
  usage
fi

echo "Please enter password"
read -s DBPW
MYSQL=`which mysql` 
DATABASES=`mysql -BN  -uSuperadm -p$DBPW -e"show databases"`
for DBNAME in $DATABASES; do if [[ $DBNAME == fp_* ]];
then
  echo $DBNAME
  if [ -n "$CMD" ]; then
    export MCMD="$MYSQL -uSuperadm -p$DBPW $DBNAME -e \"$CMD\""
  else
    export MCMD="$MYSQL -uSuperadm -p$DBPW $DBNAME  < $INFILE"
  fi
  eval $MCMD
fi
done


