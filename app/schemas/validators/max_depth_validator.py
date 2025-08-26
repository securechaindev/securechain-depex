def validate_max_depth(max_depth: int) -> int:
    if max_depth < 1 and max_depth != -1:
        raise ValueError("max_depth must be greater than or equal to 1, or exactly -1. Being -1 a special value that indicates no limit.")
    return max_depth
