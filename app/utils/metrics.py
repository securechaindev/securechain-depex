async def mean(impacts: list[float]) -> float:
    if impacts:
        return sum(impacts) / len(impacts)
    return 0.


async def weighted_mean(impacts: list[float]) -> float:
    if impacts:
        dividends = []
        divisors = []

        for var in impacts:
            dividends.append(var**2 * 0.1)
            divisors.append(var * 0.1)

        return sum(dividends) / sum(divisors)
    return 0.