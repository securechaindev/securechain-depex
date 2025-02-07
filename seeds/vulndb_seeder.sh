#!/bin/bash

HAVE_DATA=$(mongosh --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb nvd --eval "db.getCollection('cves').countDocuments({}) != 0")

if [ $HAVE_DATA == true ]; then
    echo "The database is not empty, no data will be imported"
else
    mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip --nsInclude=nvd.* --dir=./seeds/vuln/
    mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip --nsInclude=depex.* --dir=./seeds/vuln/
fi
