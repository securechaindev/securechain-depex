def validate_max_level(max_level: int) -> int:
    if max_level < 1 and max_level != -1:
        raise ValueError("max_level must be greater than or equal to 1, or exactly -1. Being -1 a special value that indicates no limit.")
    return max_level
