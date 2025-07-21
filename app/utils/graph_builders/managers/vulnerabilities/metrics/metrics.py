async def mean(impacts: list[float]) -> float:
    if impacts:
        return round(sum(impacts) / len(impacts), 2)
    return 0.0


async def weighted_mean(impacts: list[float]) -> float:
    if impacts:
        return round(sum(var**2 * 0.1 for var in impacts) / sum(var * 0.1 for var in impacts), 2)
    return 0.0
