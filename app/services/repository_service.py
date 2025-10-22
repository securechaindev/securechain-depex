from datetime import datetime
from typing import Any

from app.database import DatabaseManager


class RepositoryService:
    def __init__(self, db: DatabaseManager):
        self._driver = db.get_neo4j_driver()

    async def create_repository(self, repository: dict[str, Any]) -> str:
        query = """
        MATCH(u:User) WHERE u._id = $user_id
        MERGE(r: Repository{
            owner: $owner,
            name: $name,
            moment: $moment,
            is_complete: $is_complete
        })
        CREATE (u)-[rel:OWN]->(r)
        RETURN elementid(r) AS id
        """
        async with self._driver.session() as session:
            result = await session.run(query, repository)
            record = await result.single()
        return record[0] if record else None

    async def create_user_repository_rel(self, repository_id: str, user_id: str) -> None:
        query = """
        MATCH(u:User) WHERE u._id = $user_id
        MATCH(r:Repository) WHERE elementid(r) = $repository_id
        MERGE (u)-[rel:OWN]->(r)
        RETURN elementid(r) AS id
        """
        async with self._driver.session() as session:
            result = await session.run(query, repository_id=repository_id, user_id=user_id)
            record = await result.single()
        return record["id"]

    async def read_repository_by_owner_and_name(self, owner: str, name: str) -> dict[str, Any] | None:
        query = """
        MATCH(r: Repository{owner: $owner, name: $name})
        RETURN r{{id: elementid(r), .*}} AS repository
        """
        async with self._driver.session() as session:
            result = await session.run(query, owner=owner, name=name)
            record = await result.single()
        return record["repository"] if record else None

    async def read_repositories_by_user_id(self, user_id: str) -> dict[str, Any]:
        query = """
        MATCH (u:User)-[]->(r:Repository)-[rel:USE]->(rf:RequirementFile)
        WHERE u._id = $user_id
        WITH r, collect({name: rf.name, manager: rf.manager, requirement_file_id: elementid(rf)}) as requirement_files
        RETURN collect({
            owner: r.owner,
            name: r.name,
            is_complete: r.is_complete,
            requirement_files: requirement_files
        })
        """
        repositories = []
        async with self._driver.session() as session:
            result = await session.run(query, user_id=user_id)
            record = await result.single()
            repositories.extend(record[0] if record else [])
        return repositories

    async def update_repository_is_complete(self, repository_id: str, is_complete: bool) -> None:
        query = """
        MATCH (r:Repository) WHERE elementid(r) = $repository_id
        SET r.is_complete = $is_complete
        """
        async with self._driver.session() as session:
            await session.run(query, repository_id=repository_id, is_complete=is_complete)

    async def update_repository_moment(self, repository_id: str) -> None:
        query = """
        MATCH (r:Repository) WHERE elementid(r) = $repository_id
        SET r.moment = $moment
        """
        async with self._driver.session() as session:
            await session.run(query, repository_id=repository_id, moment=datetime.now())
