#!/bin/bash

neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true

neo4j console
