from pymongo import ASCENDING

from app.services import (
    cve_collection,
    package_collection,
    version_collection,
    depex_package_edge_collection,
    pypi_package_edge_collection
)


async def create_indexes() -> None:
    await package_collection.create_index('name', unique=True)

    await depex_package_edge_collection.create_index(
        [
            ('package_name', ASCENDING),
            ('constraints', ASCENDING)
        ],
        unique=True
    )

    await pypi_package_edge_collection.create_index(
        [
            ('package_name', ASCENDING),
            ('constraints', ASCENDING)
        ],
        unique=True
    )

    await cve_collection.create_index('id', unique=True)
    await cve_collection.create_index(
        [
            ('id', ASCENDING),
            ('configurations.nodes.cpeMatch.criteria', ASCENDING)
        ],
        unique=True
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
        unique=True
    )
    await version_collection.create_index(
        [
            ('count', ASCENDING),
            ('package', ASCENDING)
        ],
        unique=True
    )