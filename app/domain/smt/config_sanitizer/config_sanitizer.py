from __future__ import annotations

from z3 import IntNumRef, ModelRef, RatNumRef

from app.dependencies import ServiceContainer
from app.services import VersionService


class ConfigSanitizer:
    instance: ConfigSanitizer | None = None
    initialized: bool = False

    def __new__(cls) -> ConfigSanitizer:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        if not ConfigSanitizer.initialized:
            container = ServiceContainer()
            self.version_service: VersionService = container.get_version_service()
            ConfigSanitizer.initialized = True

    async def sanitize(self, node_type: str, config: ModelRef) -> dict[str, float | int]:
        final_config: dict[str, float | int] = {}
        impact_vars: dict[str, float | int] = {}

        for var in config:
            value = self.extract_variable_value(config, var)
            if value is None:
                continue

            var_name = str(var)
            if "impact_" in var_name:
                impact_vars[var_name] = value
            else:
                final_config[var_name] = value

        self.process_impact_variables(final_config, impact_vars)

        return await self.version_service.read_releases_by_serial_numbers(node_type, final_config)

    @staticmethod
    def extract_variable_value(config: ModelRef, var) -> float | int | None:
        var_name = str(var)

        if any(char in var_name for char in ("/0", "func_obj")):
            return None

        if isinstance(config[var], RatNumRef):
            return round(
                config[var].numerator_as_long() / config[var].denominator_as_long(), 2
            )

        if isinstance(config[var], IntNumRef):
            value = config[var].as_long()
            if value == -1:
                return None
            return value

        return 0

    @staticmethod
    def process_impact_variables(
        final_config: dict[str, float | int], impact_vars: dict[str, float | int]
    ) -> None:
        for impact_var, impact_value in impact_vars.items():
            base_var = impact_var.replace("impact_", "")
            if base_var in final_config:
                final_config[impact_var] = impact_value
