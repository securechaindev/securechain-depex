@echo off
for /f "usebackq tokens=*" %%i in (`grep -v "^#" .env`) do (
    set "%%i"
)

docker exec --interactive --tty pypi_neo4j gzip -d /backups/pypi_neo4j.cypher.gz  > nul 2>&1
docker exec --interactive --tty pypi_neo4j cypher-shell -u %GRAPH_DB_USER% -p %GRAPH_DB_PASSWORD_PYPI% -a bolt://localhost:7687 -f /backups/pypi_neo4j.cypher > nul 2>&1
docker exec --interactive --tty pypi_neo4j rm /backups/pypi_neo4j.cypher
echo PyPI graph database was restored
docker exec --interactive --tty npm_neo4j gzip -d /backups/npm_neo4j.cypher.gz  > nul 2>&1
docker exec --interactive --tty npm_neo4j cypher-shell -u %GRAPH_DB_USER% -p %GRAPH_DB_PASSWORD_NPM% -a bolt://localhost:7686 -f /backups/npm_neo4j.cypher > nul 2>&1
docker exec --interactive --tty npm_neo4j rm /backups/npm_neo4j.cypher
echo NPM graph database was restored
docker exec --interactive --tty maven_neo4j gzip -d /backups/maven_neo4j.cypher.gz  > nul 2>&1
docker exec --interactive --tty maven_neo4j cypher-shell -u %GRAPH_DB_USER% -p %GRAPH_DB_PASSWORD_MAVEN% -a bolt://localhost:7685 -f /backups/maven_neo4j.cypher > nul 2>&1
docker exec --interactive --tty maven_neo4j rm /backups/maven_neo4j.cypher
echo Maven graph database was restored
