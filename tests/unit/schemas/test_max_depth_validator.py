import pytest

from app.schemas.validators import validate_max_depth


class TestMaxDepthValidator:
    def test_max_depth_positive_value(self):
        result = validate_max_depth(3)
        assert result == 3

    def test_max_depth_minus_one(self):
        result = validate_max_depth(-1)
        assert result == -1

    def test_max_depth_one(self):
        result = validate_max_depth(1)
        assert result == 1

    def test_max_depth_two(self):
        result = validate_max_depth(2)
        assert result == 2

    def test_max_depth_five(self):
        result = validate_max_depth(5)
        assert result == 5

    def test_max_depth_ten(self):
        result = validate_max_depth(10)
        assert result == 10

    def test_max_depth_zero_invalid(self):
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(0)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_negative_two_invalid(self):
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(-2)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_negative_five_invalid(self):
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(-5)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_negative_ten_invalid(self):
        with pytest.raises(ValueError) as exc_info:
            validate_max_depth(-10)
        assert "max_depth must be greater than or equal to 1" in str(exc_info.value)

    def test_max_depth_large_value(self):
        result = validate_max_depth(100)
        assert result == 100

    def test_max_depth_boundary_minus_one(self):
        result = validate_max_depth(-1)
        assert result == -1

    def test_max_depth_boundary_one(self):
        result = validate_max_depth(1)
        assert result == 1
