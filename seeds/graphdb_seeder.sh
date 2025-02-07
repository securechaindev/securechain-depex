#!/bin/bash

DB_PATH="/var/lib/neo4j/data/databases/neo4j"

if [ -d "$DB_PATH" ] && [ "$(ls -A "$DB_PATH")" ]; then
    echo "The database is not empty, no data will be imported"
else
    neo4j-admin database load neo4j --from-path=/backups
fi

neo4j console
