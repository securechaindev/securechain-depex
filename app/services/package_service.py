from typing import Any

from neo4j import unit_of_work
from neo4j.exceptions import Neo4jError

from app.database import DatabaseManager
from app.exceptions import MemoryOutException


class PackageService:
    def __init__(self, db: DatabaseManager):
        self.driver = db.get_neo4j_driver()

    @staticmethod
    @unit_of_work(timeout=3)
    async def read_graph_package(tx, query, package_name, max_depth):
        result = await tx.run(
            query,
            package_name=package_name,
            max_depth=max_depth
        )
        return await result.single()

    async def read_package_status_by_name(self, node_type: str, package_name: str) -> dict[str, Any] | None:
        query = f"""
        MATCH(p:{node_type}{{name:$package_name}})-[:HAVE]->(v:Version)
        WITH p, collect(v{{.*}}) AS versions
        RETURN p{{.*, versions: versions}} AS package
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                package_name=package_name
            )
            record = await result.single()
        return record.get("package") if record else None

    async def read_version_status_by_package_and_name(self, node_type: str, package_name: str, version_name: str) -> dict[str, Any] | None:
        query = f"""
        MATCH(p:{node_type}{{name:$package_name}})-[:HAVE]->(v:Version{{name:$version_name}})
        RETURN v{{id: elementid(v), .*}} AS version
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                package_name=package_name,
                version_name=version_name
            )
            record = await result.single()
        return record.get("version") if record else None

    async def read_packages_by_requirement_file(self, requirement_file_id: str) -> dict[str, str] | None:
        query = """
        MATCH (rf:RequirementFile) WHERE elementid(rf) = $requirement_file_id
        MATCH (rf)-[requirement_rel]->(package)
        RETURN apoc.map.fromPairs(collect([package.name, requirement_rel.constraints])) AS requirement_files
        """
        async with self.driver.session() as session:
            result = await session.run(query, requirement_file_id=requirement_file_id)
            record = await result.single()
        return record.get("requirement_files") if record else None

    async def read_packages_expansion_by_version(
        self,
        version_purl: str,
    ) -> dict[str, Any] | None:
        query = """
        MATCH (:Version{purl:$version_purl})-[r:REQUIRE]->(dep)
        WITH r, collect(dep) AS dependencies
        RETURN {
            nodes: [dep IN dependencies | {
                id: dep.purl,
                label: dep.name,
                type: labels(dep)[0],
                props: {
                    name: dep.name,
                    vendor: dep.vendor,
                    repository_url: dep.repository_url,
                    purl: dep.purl
                }
            }],
            edges: [dep IN dependencies | {
                id: 'e-' + $version_purl + '-' + dep.purl,
                source: $version_purl,
                target: dep.purl,
                type: 'REQUIRE',
                props: {
                    constraints: r.constraints,
                    parent_version_name: r.parent_version_name
                }
            }]
        } AS expansion_data
        """
        async with self.driver.session() as session:
            result = await session.run(query, version_purl=version_purl)
            record = await result.single()
        return record.get("expansion_data") if record else None

    async def read_packages_expansion_by_req_file(
        self,
        requirement_file_id: str,
    ) -> dict[str, Any] | None:
        query = """
        MATCH (rf:RequirementFile)-[r:REQUIRE]->(dep)
        WHERE elementid(rf) = $requirement_file_id
        WITH collect({dep: dep, r: r}) AS items
        RETURN {
            nodes: [item IN items | {
                id: item.dep.purl,
                label: item.dep.name,
                type: labels(item.dep)[0],
                props: {
                    name: item.dep.name,
                    vendor: item.dep.vendor,
                    repository_url: item.dep.repository_url,
                    purl: item.dep.purl
                }
            }],
            edges: [item IN items | {
                id: 'e-' + $requirement_file_id + '-' + item.dep.purl,
                source: $requirement_file_id,
                target: item.dep.purl,
                type: 'REQUIRE',
                props: {
                    constraints: item.r.constraints,
                    parent_version_name: item.r.parent_version_name
                }
            }]
        } AS expansion_data
        """
        async with self.driver.session() as session:
            result = await session.run(query, requirement_file_id=requirement_file_id)
            record = await result.single()
        return record.get("expansion_data") if record else None

    async def read_graph_for_package_ssc_info_operation(
        self,
        node_type: str,
        package_name: str,
        max_depth: int
    ) -> dict[str, Any] | None:
        query = f"""
        MATCH (p:{node_type}{{name:$package_name}})
        CALL apoc.path.expandConfig(
            p,
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
            length(path) / 2 AS depth,
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
        WITH enriched_pkg, depth
        WHERE depth IS NOT NULL
        WITH
            collect(CASE WHEN depth = 1 THEN enriched_pkg END) AS direct_deps,
            collect(CASE WHEN depth > 1 THEN {{node: enriched_pkg, depth: depth}} END) AS indirect_info
        WITH
            [dep IN direct_deps WHERE dep IS NOT NULL] AS direct_deps,
            [info IN indirect_info WHERE info IS NOT NULL] AS indirect_info
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
        }} AS ssc_package_info
        """
        try:
            async with self.driver.session() as session:
                record = await session.execute_read(
                    self.read_graph_package,
                    query,
                    package_name,
                    max_depth
                )
                return record.get("ssc_package_info") if record else None
        except Neo4jError as err:
            code = getattr(err, "code", "") or ""
            if (
                code == "Neo.TransientError.General.MemoryPoolOutOfMemoryError"
                or code == "Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
                or code == "Neo.ClientError.Transaction.TransactionTimedOut"
            ):
                raise MemoryOutException() from err

    async def exists_package(self, node_type: str, package_name: str) -> bool:
        query = f"""
        RETURN EXISTS {{
            MATCH (p:{node_type}{{name: $package_name}})
        }} AS exists
        """
        async with self.driver.session() as session:
            result = await session.run(query, package_name=package_name)
            record = await result.single()
        return record.get("exists") if record else False

    async def relate_packages(self, node_type: str, req_file_id: str, packages: list[dict[str, Any]]) -> None:
        query = f"""
        MATCH (parent:RequirementFile)
        WHERE elementid(parent) = $req_file_id
        UNWIND $packages AS package
        MATCH (p: {node_type}{{name: package.name}})
        CREATE (parent)-[:REQUIRE{{constraints: package.constraints, parent_version_name: package.parent_version_name}}]->(p)
        """
        async with self.driver.session() as session:
            await session.run(query, req_file_id=req_file_id, packages=packages)
