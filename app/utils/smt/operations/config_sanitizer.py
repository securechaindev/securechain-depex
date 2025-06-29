from z3 import ModelRef, RatNumRef, IntNumRef


def config_sanitizer(config: ModelRef) -> dict[str, float | int]:
    sanitize_config: dict[str, float | int] = {}
    aux: dict[str, float | int] = {}
    for var in config:
        value: float | int = 0
        if any(char in str(var) for char in ("/0", "func_obj")):
            continue
        if isinstance(config[var], RatNumRef):
            value = round(
                config[var].numerator_as_long() / config[var].denominator_as_long(), 2
            )
        elif isinstance(config[var], IntNumRef):
            value = config[var].as_long()
            if value == -1:
                continue
        if "impact_" in str(var):
            aux[str(var)] = value
        else:
            sanitize_config[str(var)] = value
    for impact_var, impact in aux.items():
        if impact_var.replace("impact_", "") in sanitize_config:
            sanitize_config[impact_var] = impact
    return sanitize_config