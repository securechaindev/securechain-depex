#!/bin/bash

export $(grep -v '^#' .env | xargs)

docker exec --interactive --tty pip_neo4j gzip -d /backups/pip_neo4j.cypher.gz
docker exec --interactive --tty pip_neo4j cypher-shell -u $GRAPH_DB_USER -p $GRAPH_DB_PASSWORD_PIP -a bolt://localhost:7687 -f /backups/pip_neo4j.cypher > /dev/null 2>&1
docker exec --interactive --tty npm_neo4j gzip -d /backups/npm_neo4j.cypher.gz
docker exec --interactive --tty npm_neo4j cypher-shell -u $GRAPH_DB_USER -p $GRAPH_DB_PASSWORD_NPM -a bolt://localhost:7686 -f /backups/npm_neo4j.cypher > /dev/null 2>&1
docker exec --interactive --tty mvn_neo4j gzip -d /backups/mvn_neo4j.cypher.gz
docker exec --interactive --tty mvn_neo4j cypher-shell -u $GRAPH_DB_USER -p $GRAPH_DB_PASSWORD_MVN -a bolt://localhost:7685 -f /backups/mvn_neo4j.cypher > /dev/null 2>&1
