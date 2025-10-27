"""Unit tests for base schema validators."""
import pytest
from pydantic import ValidationError

from app.schemas.base_schema import (
    BaseSchemaWithMaxDepth,
    BaseSchemaWithMaxDepthMinusOne,
    BaseSchemaWithPackageName,
)


class MaxDepthSchema(BaseSchemaWithMaxDepth):
    """Test schema using BaseSchemaWithMaxDepth."""

    max_depth: int
    test_field: str = "test"


class MaxDepthMinusOneSchema(BaseSchemaWithMaxDepthMinusOne):
    """Test schema using BaseSchemaWithMaxDepthMinusOne."""

    max_depth: int
    test_field: str = "test"


class PackageNameSchema(BaseSchemaWithPackageName):
    """Test schema using BaseSchemaWithPackageName."""

    package_name: str
    test_field: str = "test"


class TestBaseSchemaWithMaxDepth:
    """Test suite for BaseSchemaWithMaxDepth validator."""

    def test_max_depth_positive_value(self):
        """Test max_depth with positive value."""
        obj = MaxDepthSchema(max_depth=3)
        # Should be transformed to multiply by 2: 3 * 2 = 6
        assert obj.max_depth == 6

    def test_max_depth_minus_one(self):
        """Test max_depth with -1 value."""
        obj = MaxDepthSchema(max_depth=-1)
        # -1 should remain -1
        assert obj.max_depth == -1

    def test_max_depth_one(self):
        """Test max_depth with value 1."""
        obj = MaxDepthSchema(max_depth=1)
        # 1 * 2 = 2
        assert obj.max_depth == 2

    def test_max_depth_large_value(self):
        """Test max_depth with large value."""
        obj = MaxDepthSchema(max_depth=10)
        # 10 * 2 = 20
        assert obj.max_depth == 20

    def test_max_depth_zero_invalid(self):
        """Test max_depth with 0 should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            MaxDepthSchema(max_depth=0)
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "max_depth" in errors[0]["loc"]
        assert "max_depth must be greater than or equal to 1" in errors[0]["msg"]

    def test_max_depth_negative_invalid(self):
        """Test max_depth with negative value (not -1) should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            MaxDepthSchema(max_depth=-5)
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "max_depth" in errors[0]["loc"]


class TestBaseSchemaWithMaxDepthMinusOne:
    """Test suite for BaseSchemaWithMaxDepthMinusOne validator."""

    def test_max_depth_positive_value(self):
        """Test max_depth with positive value using (max_depth * 2) - 1."""
        obj = MaxDepthMinusOneSchema(max_depth=3)
        # Should be transformed to (3 * 2) - 1 = 5
        assert obj.max_depth == 5

    def test_max_depth_minus_one(self):
        """Test max_depth with -1 value."""
        obj = MaxDepthMinusOneSchema(max_depth=-1)
        # -1 should remain -1
        assert obj.max_depth == -1

    def test_max_depth_one(self):
        """Test max_depth with value 1."""
        obj = MaxDepthMinusOneSchema(max_depth=1)
        # (1 * 2) - 1 = 1
        assert obj.max_depth == 1

    def test_max_depth_large_value(self):
        """Test max_depth with large value."""
        obj = MaxDepthMinusOneSchema(max_depth=10)
        # (10 * 2) - 1 = 19
        assert obj.max_depth == 19

    def test_max_depth_zero_valid(self):
        """Test max_depth with 0 - should be allowed but transformed."""
        # Note: This transformation happens before validation, so 0 becomes (0 * 2) - 1 = -1
        # Then validation sees -1 which is valid
        obj = MaxDepthMinusOneSchema(max_depth=0)
        assert obj.max_depth == -1


class TestBaseSchemaWithPackageName:
    """Test suite for BaseSchemaWithPackageName validator."""

    def test_package_name_lowercase(self):
        """Test package_name is converted to lowercase."""
        obj = PackageNameSchema(package_name="FastAPI")
        assert obj.package_name == "fastapi"

    def test_package_name_already_lowercase(self):
        """Test package_name already lowercase."""
        obj = PackageNameSchema(package_name="fastapi")
        assert obj.package_name == "fastapi"

    def test_package_name_uppercase(self):
        """Test package_name with all uppercase."""
        obj = PackageNameSchema(package_name="REQUESTS")
        assert obj.package_name == "requests"

    def test_package_name_mixed_case(self):
        """Test package_name with mixed case."""
        obj = PackageNameSchema(package_name="NumPy")
        assert obj.package_name == "numpy"

    def test_package_name_with_special_chars(self):
        """Test package_name with special characters."""
        obj = PackageNameSchema(package_name="Django-REST-Framework")
        assert obj.package_name == "django-rest-framework"

    def test_package_name_empty_allowed(self):
        """Test package_name empty - Pydantic may allow if not constrained."""
        # Note: Pydantic doesn't enforce min_length by default unless specified
        obj = PackageNameSchema(package_name="")
        assert obj.package_name == ""

    def test_package_name_numbers(self):
        """Test package_name with numbers."""
        obj = PackageNameSchema(package_name="Boto3")
        assert obj.package_name == "boto3"
