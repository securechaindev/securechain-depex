from datetime import datetime
from typing import Any

from neo4j import unit_of_work
from neo4j.exceptions import Neo4jError

from app.database import DatabaseManager
from app.exceptions import MemoryOutException


class RequirementFileService:
    def __init__(self, db: DatabaseManager):
        self.driver = db.get_neo4j_driver()

    @staticmethod
    @unit_of_work(timeout=3)
    async def read_graph_req_file(tx, query, requirement_file_id, max_depth):
        result = await tx.run(
            query,
            requirement_file_id=requirement_file_id,
            max_depth=max_depth
        )
        return await result.single()

    async def create_requirement_file(self, requirement_file: dict[str, Any], repository_id: str) -> str | None:
        query = """
        MATCH (r:Repository)
        WHERE elementid(r) = $repository_id
        CREATE (rf:RequirementFile {name:$name,manager:$manager,moment:$moment})
        CREATE (r)-[rel:USE]->(rf)
        RETURN elementid(rf) AS id
        """
        async with self.driver.session() as session:
            result = await session.run(query, requirement_file, repository_id=repository_id)
            record = await result.single()
        return record.get("id") if record else None

    async def read_requirement_files_by_repository(self, repository_id: str) -> dict[str, str] | None:
        query = """
        MATCH (r:Repository)
        WHERE elementid(r) = $repository_id
        MATCH (r)-[use_rel]->(requirement_file)
        RETURN apoc.map.fromPairs(collect([requirement_file.name, elementid(requirement_file)])) AS requirement_files
        """
        async with self.driver.session() as session:
            result = await session.run(query, repository_id=repository_id)
            record = await result.single()
        return record.get("requirement_files") if record else None

    async def read_requirement_file_moment(self, requirement_file_id: str) -> datetime | None:
        query = """
        MATCH (rf:RequirementFile)
        WHERE elementid(rf) = $requirement_file_id
        RETURN rf.moment AS moment
        """
        async with self.driver.session() as session:
            result = await session.run(query, requirement_file_id=requirement_file_id)
            record = await result.single()
        return record.get("moment") if record else None

    async def read_data_for_smt_transform(
        self,
        requirement_file_id: str,
        max_depth: int
    ) -> dict[str, Any] | None:
        query = """
        MATCH (rf:RequirementFile)
        WHERE elementid(rf) = $requirement_file_id
        CALL apoc.path.subgraphAll(rf, {relationshipFilter: '>', maxLevel: $max_depth})
        YIELD relationships
        WITH rf,
            [rel IN relationships WHERE type(rel) = 'REQUIRE' |
                {
                parent_serial_number: startNode(rel).serial_number,
                package: endNode(rel).purl,
                constraints: rel.constraints,
                parent_version_name: rel.parent_version_name,
                type: CASE WHEN rel.parent_version_name IS NULL THEN 'direct' ELSE 'indirect' END
                }
            ] AS require,
            [rel IN relationships WHERE type(rel) = 'HAVE' |
                {
                package: startNode(rel).purl,
                name: endNode(rel).name,
                serial_number: endNode(rel).serial_number,
                mean: endNode(rel).mean,
                weighted_mean: endNode(rel).weighted_mean
                }
            ] AS have
        RETURN {
            name: rf.name,
            moment: rf.moment,
            require: apoc.map.groupByMulti(apoc.coll.sortMaps(require, 'parent_serial_number'), 'type'),
            have: apoc.map.groupByMulti(apoc.coll.sortMaps(have, 'serial_number'), 'package')
        } As smt_info
        """
        try:
            async with self.driver.session() as session:
                record = await session.execute_read(
                    self.read_graph_req_file,
                    query,
                    requirement_file_id,
                    max_depth
                )
                return record.get("smt_info") if record else None
        except Neo4jError as err:
            code = getattr(err, "code", "") or ""
            if (
                code == "Neo.TransientError.General.MemoryPoolOutOfMemoryError"
                or code == "Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
                or code == "Neo.ClientError.Transaction.TransactionTimedOut"
            ):
                raise MemoryOutException() from err

    async def read_graph_for_req_file_ssc_info_operation(
        self,
        node_type: str,
        requirement_file_id: str,
        max_depth: int
    ) -> dict[str, Any] | None:
        query = f"""
        MATCH (rf:RequirementFile)
        WHERE elementid(rf) = $requirement_file_id
        CALL apoc.path.expandConfig(
            rf,
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
        }} AS ssc_req_file_info
        """
        try:
            async with self.driver.session() as session:
                record = await session.execute_read(
                    self.read_graph_req_file,
                    query,
                    requirement_file_id,
                    max_depth
                )
                return record.get("ssc_req_file_info") if record else None
        except Neo4jError as err:
            code = getattr(err, "code", "") or ""
            if (
                code == "Neo.TransientError.General.MemoryPoolOutOfMemoryError"
                or code == "Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration"
                or code == "Neo.ClientError.Transaction.TransactionTimedOut"
            ):
                raise MemoryOutException() from err

    async def update_requirement_rel_constraints(self, requirement_file_id: str, package_name: str, constraints: str) -> None:
        query = """
        MATCH (rf:RequirementFile)
        WHERE elementid(rf) = $requirement_file_id
        MATCH (rf)-[requirement_rel]->(package)
        WHERE package.name = $package_name
        SET requirement_rel.constraints = $constraints
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                requirement_file_id=requirement_file_id,
                package_name=package_name,
                constraints=constraints,
            )

    async def update_requirement_file_moment(self, requirement_file_id: str) -> None:
        query = """
        MATCH (rf: RequirementFile)
        WHERE elementid(rf) = $requirement_file_id
        SET rf.moment = $moment
        """
        async with self.driver.session() as session:
            await session.run(
                query, requirement_file_id=requirement_file_id, moment=datetime.now()
        )

    async def delete_requirement_file(self, repository_id: str, requirement_file_name: str) -> None:
        query = """
        MATCH (r:Repository)
        WHERE elementid(r) = $repository_id
        MATCH (r)-[use_rel]->(requirement_file)-[requirement_rel]->(p)
        WHERE requirement_file.name = $requirement_file_name
        DELETE requirement_rel, use_rel, requirement_file
        """
        async with self.driver.session() as session:
            await session.run(
                query, repository_id=repository_id, requirement_file_name=requirement_file_name
            )

    async def delete_requirement_file_rel(self, requirement_file_id: str, package_name: str) -> None:
        query = """
        MATCH (rf:RequirementFile)
        WHERE elementid(rf) = $requirement_file_id
        MATCH (rf)-[requirement_rel]->(package)
        WHERE package.name = $package_name
        DELETE requirement_rel
        """
        async with self.driver.session() as session:
            await session.run(
                query, requirement_file_id=requirement_file_id, package_name=package_name
            )
