async def mean(impacts: list[float]) -> float:
    if impacts:
        return sum(impacts) / len(impacts)
    return 0.0


async def weighted_mean(impacts: list[float]) -> float:
    if impacts:
        return sum(var**2 * 0.1 for var in impacts) / sum(var * 0.1 for var in impacts)
    return 0.0
