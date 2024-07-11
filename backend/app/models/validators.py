def validate_max_level(value: int) -> int:
    if value < 1 and value != -1:
        raise ValueError('max_level must be greater than or equal to 1, or exactly -1')
    return value
