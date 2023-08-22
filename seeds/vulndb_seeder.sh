#!/bin/bash

export $(grep -v '^#' .env | xargs)

mongorestore --nsInclude=cves.nvd --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/
mongorestore --nsInclude=exploits.exploit_db --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/
mongorestore --nsInclude=depex.env_variables --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host localhost --gzip ./seeds/vuln/