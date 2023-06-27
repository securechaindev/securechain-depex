export $(grep -v '^#' .env | xargs)

mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip /mongo_seed/seeds/nvd/cves.bson.gz
mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip /mongo_seed/seeds/exploits/exploits.bson.gz
mongorestore --username $VULN_DB_USER --password $VULN_DB_PASSWORD --authenticationDatabase admin --host mongodb --gzip /mongo_seed/seeds/depex/env_variables.bson.gz