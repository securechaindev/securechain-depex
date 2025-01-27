#!/bin/bash

IS_EMPTY=$(mongosh --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb nvd --eval "db.getCollection('cves').countDocuments({}) === 0")

if [ $IS_EMPTY == true ]; then
  mongorestore --nsInclude=nvd.cves --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip ./seeds/vuln/
  mongorestore --nsInclude=nvd.cpe_matchs --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip ./seeds/vuln/
  mongorestore --nsInclude=nvd.cpe_products --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip ./seeds/vuln/
  mongorestore --nsInclude=nvd.cpes --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip ./seeds/vuln/
else
  echo "The database is not empty, no data will be imported"
fi
