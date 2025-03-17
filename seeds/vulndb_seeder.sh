#!/bin/bash

HAVE_DATA=$(mongosh --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb osv --eval "db.getCollection('vulnerabilities').countDocuments({}) != 0")

if [ $HAVE_DATA == true ]; then
    echo "The database is not empty, no data will be imported"
else
    mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip --nsInclude=osv.* --dir=./seeds/vuln/
    mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip --nsInclude=depex.* --dir=./seeds/vuln/
fi
