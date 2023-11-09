#!/bin/bash

export $(grep -v '^#' .env | xargs)

mongorestore --nsInclude=nvd.cves --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/
mongorestore --nsInclude=nvd.cpe_matchs --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/
mongorestore --nsInclude=nvd.cpes --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/
mongorestore --nsInclude=exploit_db.exploits --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/
mongorestore --nsInclude=depex.env_variables --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/
