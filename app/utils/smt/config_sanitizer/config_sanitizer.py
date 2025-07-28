from z3 import IntNumRef, ModelRef, RatNumRef

from app.services import read_releases_by_serial_numbers


async def config_sanitizer(node_type: str, config: ModelRef) -> dict[str, float | int]:
    final_config: dict[str, float | int] = {}
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
            final_config[str(var)] = value
    for impact_var, impact in aux.items():
        if impact_var.replace("impact_", "") in final_config:
            final_config[impact_var] = impact
    return await read_releases_by_serial_numbers(node_type, final_config)
