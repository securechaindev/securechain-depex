from typing import Any

from neo4j import unit_of_work
from neo4j.exceptions import Neo4jError

from app.database import DatabaseManager
from app.exceptions import MemoryOutException


class VersionService:
    def __init__(self, db: DatabaseManager):
        self.driver = db.get_neo4j_driver()

    @staticmethod
    @unit_of_work(timeout=3)
    async def read_graph_version(tx, query, package_name, version_name, max_depth):
        result = await tx.run(
            query,
            package_name=package_name,
            version_name=version_name,
            max_depth=max_depth
        )
        return await result.single()

    async def read_releases_by_serial_numbers(
        self,
        node_type: str,
        config: dict[str, int]
    ) -> list[dict[str, str | float | int]]:
        query = f"""
        MATCH (v:Version)<-[:HAVE]-(parent:{node_type})
        WHERE v.serial_number = $serial_number AND parent.name = $package
        RETURN v.name
        """
        sanitized_config: dict[str, str | float | int] = {}
        for var, value in config.items():
            async with self.driver.session() as session:
                result = await session.run(query, package=var, serial_number=value)
                record = await result.single()
            if record:
                sanitized_config.update({var: record[0]})
            else:
                sanitized_config.update({var: value})
        return sanitized_config

    async def read_serial_numbers_by_releases(
        self,
        node_type: str,
        config: dict[str, str]
    ) -> dict[str, int]:
        sanitized_config: dict[str, int] = {}
        query = f"""
        MATCH (v:Version)<-[:HAVE]-(parent:{node_type})
        WHERE v.name = $release AND parent.name = $package
        RETURN v.serial_number
        """
        for package, release in config.items():
            async with self.driver.session() as session:
                result = await session.run(query, package=package, release=release)
                record = await result.single()
            if record:
                sanitized_config.update({package: record[0]})
        return sanitized_config

    async def read_graph_for_version_ssc_info_operation(
        self,
        node_type: str,
        package_name: str,
        version_name: str,
        max_depth: int
    ) -> dict[str, Any]:
        query = f"""
        MATCH (:{node_type}{{name:$package_name}})-[:HAVE]->(v:Version{{name:$version_name}})
        CALL apoc.path.expandConfig(
            v,
            {{
                relationshipFilter: 'REQUIRE>|HAVE>',
                labelFilter: 'Version|{node_type}',
                maxLevel: $max_depth,
                bfs: true,
                uniqueness: 'NODE_GLOBAL'
            }}
        ) YIELD path
        WITH
            last(nodes(path)) AS pkg,
            (length(path) + 1) / 2 AS depth,
            last(relationships(path)) AS rel
        WHERE '{node_type}' IN labels(pkg) AND type(rel) = 'REQUIRE'
        OPTIONAL MATCH (pkg:{node_type})-[:HAVE]->(v:Version)
        WITH
            pkg,
            depth,
            collect(DISTINCT {{
                name: v.name,
                mean: v.mean,
                serial_number: v.serial_number,
                weighted_mean: v.weighted_mean,
                vulnerability_count: v.vulnerabilities
            }}) AS versions,
            rel.constraints AS constraints
        WITH {{
                package_name: pkg.name,
                package_vendor: pkg.vendor,
                package_constraints: constraints,
                versions: versions
            }} AS enriched_pkg,
            depth
        WITH
            collect(CASE WHEN depth = 1 THEN enriched_pkg END) AS direct_deps,
            collect(CASE WHEN depth > 1 THEN {{node: enriched_pkg, depth: depth}} END) AS indirect_info
        WITH
            direct_deps,
            indirect_info,
            reduce(
                map = {{}},
                entry IN indirect_info |
                apoc.map.setKey(
                map,
                toString(entry.depth),
                coalesce(map[toString(entry.depth)], []) + entry.node
                )
            ) AS indirect_by_depth
        RETURN {{
            direct_dependencies: direct_deps,
            total_direct_dependencies: size(direct_deps),
            indirect_dependencies_by_depth: apoc.map.removeKey(indirect_by_depth, null),
            total_indirect_dependencies: size(indirect_info)
        }}
        """
        try:
            async with self.driver.session() as session:
                record = await session.execute_read(
                    self.read_graph_version,
                    query,
                    package_name,
                    version_name,
                    max_depth
                )
                return record[0] if record else None
        except Neo4jError as err:
            code = getattr(err, "code", "") or ""
            if (
                code == "Neo.TransientError.General.MemoryPoolOutOfMemoryError"
                or code == "Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
                or code == "Neo.ClientError.Transaction.TransactionTimedOut"
            ):
                raise MemoryOutException() from err
