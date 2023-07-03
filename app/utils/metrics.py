async def mean(impacts: list[float]) -> float:
    if impacts:
        return sum(impacts) / len(impacts)
    return 0.


async def weighted_mean(impacts: list[float]) -> float:
    if impacts:
        dividends = [var**2 * 0.1 for var in impacts]
        divisors = [var * 0.1 for var in impacts]

        return sum(dividends) / sum(divisors)
    return 0.