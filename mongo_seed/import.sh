mongorestore --host mongodb --gzip /mongo_seed/seeds/nvd/cves.bson.gz
mongorestore --host mongodb --gzip /mongo_seed/seeds/depex/env_variables.bson.gz
mongorestore --host mongodb --gzip /mongo_seed/seeds/pypi/package_edges.bson.gz
mongorestore --host mongodb --gzip /mongo_seed/seeds/pypi/packages.bson.gz
mongorestore --host mongodb --gzip /mongo_seed/seeds/pypi/versions.bson.gz