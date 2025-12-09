from z3 import IntNumRef, ModelRef, RatNumRef

from app.dependencies import ServiceContainer
from app.services import VersionService


class ConfigSanitizer:
    instance: ConfigSanitizer | None = None
    version_service: VersionService | None = None

    def __new__(cls) -> ConfigSanitizer:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            container = ServiceContainer()
            cls.version_service = container.get_version_service()
        return cls.instance

    async def sanitize(self, node_type: str, config: ModelRef) -> dict[str, str | float]:
        impact_config: dict[str, float] = {}
        version_config: dict[str, int] = {}
        impact_vars: dict[str, float] = {}

        for var in config:
            value = self.extract_variable_value(config, var)
            if value is None:
                continue

            var_name = str(var)
            if "impact_" in var_name and isinstance(value, float):
                impact_vars[var_name] = value
            elif isinstance(value, int):
                version_config[var_name] = value

        self.process_impact_variables(impact_config, impact_vars)

        assert self.version_service is not None
        final_version_config = await self.version_service.read_releases_by_serial_numbers(node_type, version_config)

        return {**final_version_config, **impact_config}

    @staticmethod
    def extract_variable_value(config: ModelRef, var) -> int | float | None:
        var_name = str(var)

        if any(char in var_name for char in ("/0", "func_obj")):
            return None
        
        value = config[var]

        if isinstance(value, RatNumRef):
            return round(
                value.numerator_as_long() / value.denominator_as_long(), 2
            )

        if isinstance(value, IntNumRef):
            value = value.as_long()
            if value == -1:
                return None
            return value

        return 0

    @staticmethod
    def process_impact_variables(
        impact_config: dict[str, float],
        impact_vars: dict[str, float]
    ) -> None:
        for impact_var, impact_value in impact_vars.items():
            base_var = impact_var.replace("impact_", "")
            if base_var in impact_config:
                impact_config[impact_var] = impact_value
