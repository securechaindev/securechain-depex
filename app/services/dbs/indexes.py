from app.services.dbs.databases import (
    cve_collection,
    version_collection,
    package_collection
)

from pymongo import ASCENDING


async def create_indexes() -> None:
    await package_collection.create_index('name', unique = True)

    await cve_collection.create_index('id', unique = True)
    await cve_collection.create_index(
        [
            ('id', ASCENDING),
            ('configurations.nodes.cpeMatch.criteria', ASCENDING)
        ],
        unique = True
    )

    await version_collection.create_index(
        [
            ('package', ASCENDING),
            ('mayor', ASCENDING),
            ('minor', ASCENDING),
            ('pacth', ASCENDING),
            ('build_numnber', ASCENDING)
        ]
    )
    await version_collection.create_index(
        [
            ('release', ASCENDING),
            ('package', ASCENDING)
        ],
        unique = True
    )