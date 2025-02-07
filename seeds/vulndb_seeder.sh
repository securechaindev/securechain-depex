#!/bin/bash

IS_EMPTY=$(mongosh --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb nvd --eval "db.getCollection('cves').countDocuments({}) === 0")

if [ $IS_EMPTY == true ]; then
    mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip --nsInclude=nvd.* --dir=./seeds/vuln/
    mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip --nsInclude=depex.* --dir=./seeds/vuln/
else
  echo "The database is not empty, no data will be imported"
fi
