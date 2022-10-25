mongorestore --host mongodb --gzip --db nvd --collection cves /mongo_seed/seeds/cves.bson.gz
mongorestore --host mongodb --gzip --db depex --collection env_variables /mongo_seed/seeds/env_variables.bson.gz
# mongorestore --host mongodb --gzip --db pypi --collection package_edges /mongo_seed/seeds/package_edges.bson.gz
# mongorestore --host mongodb --gzip --db pypi --collection packages /mongo_seed/seeds/packages.bson.gz
# mongorestore --host mongodb --gzip --db pypi --collection versions /mongo_seed/seeds/versions.bson.gz