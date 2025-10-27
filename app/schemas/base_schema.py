from pydantic import BaseModel, field_validator, model_validator

from app.schemas.validators import validate_max_depth


class BaseSchemaWithMaxDepth(BaseModel):
    @field_validator("max_depth")
    def validate_max_depth(cls, value):
        return validate_max_depth(value)

    @model_validator(mode='before')
    def set_max_depth_to_square(cls, values):
        if values.get('max_depth') != -1:
            values['max_depth'] = values.get('max_depth', 1) * 2
        return values


class BaseSchemaWithMaxDepthMinusOne(BaseModel):
    @field_validator("max_depth")
    def validate_max_depth(cls, value):
        return validate_max_depth(value)

    @model_validator(mode='before')
    def set_max_depth_to_square(cls, values):
        if values.get('max_depth') != -1:
            values['max_depth'] = (values.get('max_depth', 1) * 2) - 1
        return values


class BaseSchemaWithPackageName(BaseModel):
    @model_validator(mode='before')
    def set_package_name_to_lowercase(cls, values):
        if 'package_name' in values:
            values['package_name'] = values['package_name'].lower()
        return values
