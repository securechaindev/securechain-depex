from app.domain.repo_analyzer.requirement_files.pypi_utils import PyPiConstraintParser


class TestPyPiConstraintParser:
    def test_get_first_op_position_with_operator(self):
        result = PyPiConstraintParser.get_first_op_position("package>=1.0.0", ["<", ">", "="])
        assert result == 7

    def test_get_first_op_position_without_operator(self):
        result = PyPiConstraintParser.get_first_op_position("package", ["<", ">", "="])
        assert result == 7

    def test_get_first_op_position_at_start(self):
        result = PyPiConstraintParser.get_first_op_position(">=1.0.0", [">", "=", "<"])
        assert result == 0

    def test_get_first_op_position_no_operators(self):
        result = PyPiConstraintParser.get_first_op_position("1.0.0", [">", "<"])
        assert result == 5

    def test_parse_pypi_constraints_simple(self):
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0")
        assert result == ">= 1.0.0"

    def test_parse_pypi_constraints_multiple(self):
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0,<2.0.0")
        assert ">=" in result and "<" in result

    def test_parse_constraints_with_multiple_commas(self):
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0,<2.0.0,!=1.5.0")
        assert ">=" in result
        assert "<" in result
        assert "!=" in result

    def test_parse_pypi_constraints_empty(self):
        result = PyPiConstraintParser.parse_pypi_constraints("")
        assert result == "any"

    def test_parse_constraints_none(self):
        result = PyPiConstraintParser.parse_pypi_constraints(None)
        assert result == "any"

    def test_parse_constraints_with_or(self):
        result = PyPiConstraintParser.parse_pypi_constraints(">=1.0.0 || 2.0.0")
        assert "!=" in result

    def test_clean_pypi_constraints_equality(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["==1.0.0"])
        assert result == "==1.0.0"

    def test_clean_pypi_constraints_range(self):
        result = PyPiConstraintParser.clean_pypi_constraints([">=1.0.0", "<2.0.0"])
        assert ">= 1.0.0" in result and "< 2.0.0" in result

    def test_clean_pypi_constraints_compatible_release(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["~=1.4.2"])
        assert ">=1.4.2" in result
        assert "<1.5" in result

    def test_clean_pypi_constraints_wildcard(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["==1.4.*"])
        assert ">=1.4" in result

    def test_clean_constraints_wildcard_version(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["==1.2.*"])
        assert ">=" in result
        assert "<" in result

    def test_clean_constraints_not_equal_wildcard(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["!=1.2.*"])
        assert "<" in result or ">=" in result

    def test_clean_constraints_simple_equal(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["=1.0.0"])
        assert "==" in result

    def test_clean_constraints_no_space(self):
        result = PyPiConstraintParser.clean_pypi_constraints([">=1.0.0"])
        assert ">= 1.0.0" in result

    def test_clean_constraints_alpha_only(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["latest"])
        assert result == ""

    def test_clean_constraints_exception_handling(self):
        result = PyPiConstraintParser.clean_pypi_constraints(["invalid!@#$%"])
        assert result == "any" or result == ""
