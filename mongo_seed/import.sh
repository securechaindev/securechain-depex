mongoimport --host mongodb --db pypi --collection package_edges --file /mongo_seed/seeds/package_edges.json --jsonArray --batchSize 100000
mongoimport --host mongodb --db pypi --collection packages --file /mongo_seed/seeds/packages.json --jsonArray --batchSize 100000
mongoimport --host mongodb --db pypi --collection versions --file /mongo_seed/seeds/versions.json --jsonArray --batchSize 100000
mongoimport --host mongodb --db nvd --collection cves --file /mongo_seed/seeds/cves.json --jsonArray --batchSize 100000
mongoimport --host mongodb --db depex --collection env_variables --file /mongo_seed/seeds/env_variables.json