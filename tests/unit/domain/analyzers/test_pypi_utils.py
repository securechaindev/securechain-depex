"""Unit tests for PyPiConstraintParser."""

from app.domain.repo_analyzer.requirement_files.pypi_utils import PyPiConstraintParser


class TestPyPiConstraintParser:
    """Test suite for PyPiConstraintParser."""

    # ===== get_first_op_position tests =====

    def test_get_first_op_position_with_operator(self):
        """Test finding first operator position when operators exist."""
        result = PyPiConstraintParser.get_first_op_position("package>=1.0.0", ["<", ">", "="])
        assert result == 7

    def test_get_first_op_position_without_operator(self):
        """Test when no operator is found."""
        result = PyPiConstraintParser.get_first_op_position("package", ["<", ">", "="])
        assert result == 7

    def test_get_first_op_position_at_start(self):
        """Test getting first operator position when operator is at start."""
        result = PyPiConstraintParser.get_first_op_position(">=1.0.0", [">", "=", "<"])
        assert result == 0  # First char is >

    def test_get_first_op_position_no_operators(self):
        """Test getting first operator position when no operators exist."""
        result = PyPiConstraintParser.get_first_op_position("1.0.0", [">", "<"])
        assert result == 5  # Length of string

    # ===== parse_pypi_constraints tests =====

    def test_parse_pypi_constraints_simple(self):
        """Test parsing simple constraints."""
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0")
        assert result == ">= 1.0.0"

    def test_parse_pypi_constraints_multiple(self):
        """Test parsing multiple constraints."""
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0,<2.0.0")
        assert ">=" in result and "<" in result

    def test_parse_constraints_with_multiple_commas(self):
        """Test parsing constraints with multiple comma-separated values."""
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0,<2.0.0,!=1.5.0")
        assert ">=" in result
        assert "<" in result
        assert "!=" in result

    def test_parse_pypi_constraints_empty(self):
        """Test parsing empty constraints."""
        result = PyPiConstraintParser.parse_pypi_constraints("")
        assert result == "any"

    def test_parse_constraints_none(self):
        """Test parsing None constraints."""
        result = PyPiConstraintParser.parse_pypi_constraints(None)
        assert result == "any"

    def test_parse_constraints_with_or(self):
        """Test parsing constraints with OR operator (||)."""
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0 || 2.0.0")
        # Should convert || to !=
        assert "!=" in result

    # ===== clean_pypi_constraints tests =====

    def test_clean_pypi_constraints_equality(self):
        """Test cleaning equality constraints."""
        result = PyPiConstraintParser.clean_pypi_constraints(["==1.0.0"])
        assert result == "==1.0.0"

    def test_clean_pypi_constraints_range(self):
        """Test cleaning range constraints."""
        result = PyPiConstraintParser.clean_pypi_constraints([">=1.0.0", "<2.0.0"])
        assert ">= 1.0.0" in result and "< 2.0.0" in result

    def test_clean_pypi_constraints_compatible_release(self):
        """Test cleaning compatible release (~=)."""
        result = PyPiConstraintParser.clean_pypi_constraints(["~=1.4.2"])
        assert ">=1.4.2" in result
        assert "<1.5" in result

    def test_clean_pypi_constraints_wildcard(self):
        """Test cleaning wildcard constraints."""
        result = PyPiConstraintParser.clean_pypi_constraints(["==1.4.*"])
        assert ">=1.4" in result

    def test_clean_constraints_wildcard_version(self):
        """Test cleaning wildcard version constraints."""
        result = PyPiConstraintParser.clean_pypi_constraints(["==1.2.*"])
        # Should convert to >= and <
        assert ">=" in result
        assert "<" in result

    def test_clean_constraints_not_equal_wildcard(self):
        """Test cleaning not-equal wildcard constraints."""
        result = PyPiConstraintParser.clean_pypi_constraints(["!=1.2.*"])
        # Should convert to < and >=
        assert "<" in result or ">=" in result

    def test_clean_constraints_simple_equal(self):
        """Test cleaning simple equal constraints."""
        result = PyPiConstraintParser.clean_pypi_constraints(["=1.0.0"])
        # Should convert = to ==
        assert "==" in result

    def test_clean_constraints_no_space(self):
        """Test cleaning constraints without spaces."""
        result = PyPiConstraintParser.clean_pypi_constraints([">=1.0.0"])
        assert ">= 1.0.0" in result

    def test_clean_constraints_alpha_only(self):
        """Test cleaning constraints that are alpha only (should skip)."""
        result = PyPiConstraintParser.clean_pypi_constraints(["latest"])
        assert result == ""

    def test_clean_constraints_exception_handling(self):
        """Test that exceptions during cleaning return 'any'."""
        result = PyPiConstraintParser.clean_pypi_constraints(["invalid!@#$%"])
        assert result == "any" or result == ""
