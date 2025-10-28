import pytest
from pydantic import ValidationError

from app.schemas.base_schema import (
    BaseSchemaWithMaxDepth,
    BaseSchemaWithMaxDepthMinusOne,
    BaseSchemaWithPackageName,
)


class MaxDepthSchema(BaseSchemaWithMaxDepth):
    max_depth: int
    test_field: str = "test"


class MaxDepthMinusOneSchema(BaseSchemaWithMaxDepthMinusOne):
    max_depth: int
    test_field: str = "test"


class PackageNameSchema(BaseSchemaWithPackageName):
    package_name: str
    test_field: str = "test"


class TestBaseSchemaWithMaxDepth:
    def test_max_depth_positive_value(self):
        obj = MaxDepthSchema(max_depth=3)
        assert obj.max_depth == 6

    def test_max_depth_minus_one(self):
        obj = MaxDepthSchema(max_depth=-1)
        assert obj.max_depth == -1

    def test_max_depth_one(self):
        obj = MaxDepthSchema(max_depth=1)
        assert obj.max_depth == 2

    def test_max_depth_large_value(self):
        obj = MaxDepthSchema(max_depth=10)
        assert obj.max_depth == 20

    def test_max_depth_zero_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            MaxDepthSchema(max_depth=0)
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "max_depth" in errors[0]["loc"]
        assert "max_depth must be greater than or equal to 1" in errors[0]["msg"]

    def test_max_depth_negative_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            MaxDepthSchema(max_depth=-5)
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "max_depth" in errors[0]["loc"]


class TestBaseSchemaWithMaxDepthMinusOne:
    def test_max_depth_positive_value(self):
        obj = MaxDepthMinusOneSchema(max_depth=3)
        assert obj.max_depth == 5

    def test_max_depth_minus_one(self):
        obj = MaxDepthMinusOneSchema(max_depth=-1)
        assert obj.max_depth == -1

    def test_max_depth_one(self):
        obj = MaxDepthMinusOneSchema(max_depth=1)
        assert obj.max_depth == 1

    def test_max_depth_large_value(self):
        obj = MaxDepthMinusOneSchema(max_depth=10)
        assert obj.max_depth == 19

    def test_max_depth_zero_valid(self):
        obj = MaxDepthMinusOneSchema(max_depth=0)
        assert obj.max_depth == -1


class TestBaseSchemaWithPackageName:
    def test_package_name_lowercase(self):
        obj = PackageNameSchema(package_name="FastAPI")
        assert obj.package_name == "fastapi"

    def test_package_name_already_lowercase(self):
        obj = PackageNameSchema(package_name="fastapi")
        assert obj.package_name == "fastapi"

    def test_package_name_uppercase(self):
        obj = PackageNameSchema(package_name="REQUESTS")
        assert obj.package_name == "requests"

    def test_package_name_mixed_case(self):
        obj = PackageNameSchema(package_name="NumPy")
        assert obj.package_name == "numpy"

    def test_package_name_with_special_chars(self):
        obj = PackageNameSchema(package_name="Django-REST-Framework")
        assert obj.package_name == "django-rest-framework"

    def test_package_name_empty_allowed(self):
        obj = PackageNameSchema(package_name="")
        assert obj.package_name == ""

    def test_package_name_numbers(self):
        obj = PackageNameSchema(package_name="Boto3")
        assert obj.package_name == "boto3"
