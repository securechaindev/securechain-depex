"""Unit tests for max_depth validator utility."""
import pytest

from app.schemas.validators import validate_max_depth


class TestMaxDepthValidator:
    """Test suite for validate_max_depth function."""

    def test_max_depth_positive_value(self):
        """Test max_depth with positive value."""
        result = validate_max_depth(3)
        # validate_max_depth just validates, doesn't transform
        assert result == 3

    def test_max_depth_minus_one(self):
        """Test max_depth with -1 value."""
        result = validate_max_depth(-1)
        # -1 should be valid and remain -1
        assert result == -1

    def test_max_depth_one(self):
        """Test max_depth with value 1."""
        result = validate_max_depth(1)
        # Should remain 1
        assert result == 1

    def test_max_depth_two(self):
        """Test max_depth with value 2."""
        result = validate_max_depth(2)
        # Should remain 2
        assert result == 2

    def test_max_depth_five(self):
        """Test max_depth with value 5."""
        result = validate_max_depth(5)
        # Should remain 5
        assert result == 5

    def test_max_depth_ten(self):
        """Test max_depth with value 10."""
        result = validate_max_depth(10)
        # Should remain 10
        assert result == 10

    def test_max_depth_zero_invalid(self):
        """Test max_depth with 0 should raise error."""
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(0)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_negative_two_invalid(self):
        """Test max_depth with -2 should raise error."""
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(-2)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_negative_five_invalid(self):
        """Test max_depth with -5 should raise error."""
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(-5)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_negative_ten_invalid(self):
        """Test max_depth with -10 should raise error."""
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(-10)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_large_value(self):
        """Test max_depth with large value."""
        result = validate_max_depth(100)
        # Should remain 100
        assert result == 100

    def test_max_depth_boundary_minus_one(self):
        """Test max_depth boundary condition at -1."""
        result = validate_max_depth(-1)
        assert result == -1

    def test_max_depth_boundary_one(self):
        """Test max_depth boundary condition at 1."""
        result = validate_max_depth(1)
        assert result == 1
