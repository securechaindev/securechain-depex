from pkg_resources import parse_version

from app.managers.pypi import get_all_versions

from app.utils.operators import ops


def filter_versions(pkg_name: str, constraints) -> list[dict[str, str]]:
    distributions = list()

    all_versions = get_all_versions(pkg_name)

    if constraints:
        for version in all_versions:
            release_all = version['release']
            checkers = list()

            for constraint in constraints:
                if constraint.__contains__('Any'):
                    continue

                op, release_ctc = constraint.split(' ')

                checkers.append(ops[op](parse_version(release_all), parse_version(release_ctc)))

            if all(checkers):
                distributions.append(version)
    else:
        distributions = all_versions

    return distributions