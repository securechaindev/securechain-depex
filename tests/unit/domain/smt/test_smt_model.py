"""Unit tests for SMTModel."""
import pytest

from app.domain.smt.model import SMTModel


class TestSMTModel:
    """Test suite for SMTModel."""

    @pytest.fixture
    def sample_source_data(self):
        """Sample source data for SMTModel."""
        return {
            "name": "test-file",
            "moment": "2025-10-27T00:00:00",
            "require": {
                "direct": [
                    {
                        "package": "fastapi",
                        "constraints": ">= 0.100.0",
                    }
                ],
                "indirect": []
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 3.0, "name": "0.101.0"},
                    {"serial_number": 102, "mean": 7.0, "name": "0.102.0"}
                ]
            }
        }

    @pytest.fixture
    def indirect_source_data(self):
        """Source data with indirect dependencies."""
        return {
            "name": "requirements.txt",
            "moment": "2025-10-27T00:00:00",
            "require": {
                "direct": [
                    {"package": "fastapi", "constraints": ">= 0.100.0"}
                ],
                "indirect": [
                    {
                        "package": "pydantic",
                        "constraints": ">= 2.0.0",
                        "parent_version_name": "fastapi",
                        "parent_serial_number": 100
                    }
                ]
            },
            "have": {
                "fastapi": [
                    {"serial_number": 100, "mean": 5.0, "name": "0.100.0"},
                    {"serial_number": 101, "mean": 3.0, "name": "0.101.0"}
                ],
                "pydantic": [
                    {"serial_number": 200, "mean": 2.0, "name": "2.0.0"},
                    {"serial_number": 201, "mean": 1.5, "name": "2.1.0"}
                ]
            }
        }

    # ===== Initialization Tests =====

    def test_init(self, sample_source_data):
        """Test SMTModel initialization."""
        model = SMTModel(sample_source_data, "PyPIPackage", "mean")
        assert model.source_data == sample_source_data
        assert model.aggregator == "mean"
        assert model.node_type == "PyPIPackage"
        assert model.domain is None
        assert model.func_obj is None
        assert isinstance(model.impacts, set)
        assert isinstance(model.childs, dict)
        assert isinstance(model.parents, dict)
        assert isinstance(model.directs, list)

    # ===== Convert Tests =====

    def test_convert_parses_model_text(self, sample_source_data):
        """Test converting SMT text to domain."""
        model = SMTModel(sample_source_data, "PyPIPackage", "mean")
        model_text = model.transform()

        # Create a new model and convert it
        model2 = SMTModel(sample_source_data, "PyPIPackage", "mean")
        model2.convert(model_text)
        assert model2.domain is not None
        assert model2.func_obj is not None

    def test_convert_with_unknown_name(self):
        """Test convert when source_data has no name."""
        model = SMTModel({}, "PyPIPackage", "mean")
        model_text = "(declare-const test Real) (assert true)"
        model.convert(model_text)
        assert model.domain is not None
        assert model.func_obj is not None

    # ===== Transform Tests =====

    def test_transform_creates_domain(self, sample_source_data):
        """Test that transform creates domain."""
        model = SMTModel(sample_source_data, "PyPIPackage", "mean")
        model_text = model.transform()
        assert model.domain is not None
        assert model.func_obj is not None
        assert isinstance(model_text, str)
        assert "file_risk_test-file" in model_text

    def test_transform_with_direct_and_indirect(self, indirect_source_data):
        """Test transform with both direct and indirect dependencies."""
        model = SMTModel(indirect_source_data, "PyPIPackage", "mean")
        model_text = model.transform()

        assert model.domain is not None
        assert "|fastapi|" in model.directs
        assert "pydantic" in model.indirect_vars
        assert "file_risk_requirements.txt" in model_text

    def test_transform_with_no_requirements(self):
        """Test transform with no requirements."""
        data = {
            "name": "empty-file",
            "require": {},
            "have": {}
        }
        model = SMTModel(data, "PyPIPackage", "mean")
        model_text = model.transform()

        assert model.domain is not None
        assert len(model.directs) == 0
        assert "file_risk_empty-file" in model_text

    # ===== Direct Package Tests =====

    def test_transform_direct_package(self, sample_source_data):
        """Test transforming direct package."""
        model = SMTModel(sample_source_data, "PyPIPackage", "mean")
        require = sample_source_data["require"]["direct"][0]
        model.transform_direct_package(require)

        assert "|fastapi|" in model.directs
        assert "|impact_fastapi|" in model.impacts
        assert "fastapi" in model.filtered_versions

    def test_transform_direct_package_no_versions(self):
        """Test transforming direct package with no matching versions."""
        data = {
            "name": "test",
            "have": {
                "fastapi": []
            }
        }
        model = SMTModel(data, "PyPIPackage", "mean")
        require = {"package": "fastapi", "constraints": ">= 999.0.0"}
        model.transform_direct_package(require)

        assert "|fastapi|" in model.directs
        assert "fastapi" in model.filtered_versions

    # ===== Indirect Package Tests =====

    def test_transform_indirect_package(self, indirect_source_data):
        """Test transforming indirect package."""
        model = SMTModel(indirect_source_data, "PyPIPackage", "mean")

        # First process direct dependency
        direct_require = indirect_source_data["require"]["direct"][0]
        model.transform_direct_package(direct_require)

        # Then process indirect dependency
        indirect_require = indirect_source_data["require"]["indirect"][0]
        model.transform_indirect_package(indirect_require)

        assert "pydantic" in model.filtered_versions
        assert len(model.parents) > 0 or len(model.childs) > 0

    def test_transform_indirect_package_parent_not_filtered(self):
        """Test indirect package when parent is not in filtered versions."""
        data = {
            "name": "test",
            "have": {
                "parent": [{"serial_number": 1, "mean": 1.0, "name": "1.0.0"}],
                "child": [{"serial_number": 2, "mean": 2.0, "name": "2.0.0"}]
            }
        }
        model = SMTModel(data, "PyPIPackage", "mean")
        require = {
            "package": "child",
            "constraints": ">= 2.0.0",
            "parent_version_name": "parent",
            "parent_serial_number": 999  # Not in filtered versions
        }

        model.transform_indirect_package(require)
        assert "child" in model.filtered_versions

    # ===== Version Filtering Tests =====

    def test_get_filtered_versions_impacts(self, sample_source_data):
        """Test getting filtered versions with impacts."""
        model = SMTModel(sample_source_data, "PyPIPackage", "mean")
        versions_impacts = model.get_filtered_versions_impacts("fastapi", ">= 0.100.0")

        assert isinstance(versions_impacts, dict)
        assert len(versions_impacts) > 0
        assert all(isinstance(k, int) for k in versions_impacts.keys())

    def test_get_filtered_versions_impacts_no_package(self):
        """Test filtering versions for non-existent package."""
        data = {"name": "test", "have": {}}
        model = SMTModel(data, "PyPIPackage", "mean")
        versions_impacts = model.get_filtered_versions_impacts("nonexistent", ">= 1.0.0")

        assert isinstance(versions_impacts, dict)
        assert len(versions_impacts) == 0

    # ===== Transform Versions Tests =====

    def test_transform_versions_direct(self, sample_source_data):
        """Test transform_versions for direct dependency."""
        model = SMTModel(sample_source_data, "PyPIPackage", "mean")
        versions = {100: 5.0, 101: 3.0}
        model.transform_versions(versions, "fastapi", None)

        assert "fastapi" in model.ctcs
        assert len(model.ctcs["fastapi"]) > 0

    def test_transform_versions_indirect_with_parent(self, indirect_source_data):
        """Test transform_versions for indirect dependency with valid parent."""
        model = SMTModel(indirect_source_data, "PyPIPackage", "mean")

        # Setup filtered versions for parent
        model.filtered_versions["fastapi"] = [100, 101]

        versions = {200: 2.0, 201: 1.5}
        require = {
            "package": "pydantic",
            "parent_version_name": "fastapi",
            "parent_serial_number": 100
        }

        model.transform_versions(versions, "pydantic", require)

        assert "pydantic" in model.indirect_vars
        assert "|impact_pydantic|" in model.impacts

    def test_transform_versions_indirect_parent_not_in_filtered(self):
        """Test transform_versions when parent not in filtered versions."""
        model = SMTModel({"name": "test", "have": {}}, "PyPIPackage", "mean")

        versions = {200: 2.0}
        require = {
            "package": "pydantic",
            "parent_version_name": "fastapi",
            "parent_serial_number": 999
        }

        # Don't add fastapi to filtered_versions
        model.transform_versions(versions, "pydantic", require)

        # Should not add to ctcs since parent not found
        assert "pydantic" not in model.ctcs

    # ===== Constraint Building Tests =====

    def test_build_direct_constraint(self):
        """Test building direct constraint."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        model.build_direct_constraint("fastapi", [100, 101, 102])

        assert "fastapi" in model.ctc_domain

    def test_build_direct_constraint_empty(self):
        """Test building direct constraint with empty versions."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        model.build_direct_constraint("fastapi", [])

        assert "false" in model.ctc_domain

    def test_build_indirect_constraints(self):
        """Test building indirect constraints."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        model.childs = {"(= |child| 1)": {"parent": {100, 101}}}
        model.parents = {"child": {"parent": {100}}}

        model.build_indirect_constraints()

        assert "=>" in model.ctc_domain

    def test_build_impact_constraints(self):
        """Test building impact constraints."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        model.ctcs = {"fastapi": {5.0: {100}, 3.0: {101}}}

        model.build_impact_constraints()

        assert "impact_fastapi" in model.ctc_domain

    # ===== Helper Methods Tests =====

    def test_append_indirect_constraint(self):
        """Test appending indirect constraint."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        model.filtered_versions = {"parent": [100, 101]}

        model.append_indirect_constraint("child", [200, 201], "parent", 100)

        assert len(model.childs) > 0

    def test_append_indirect_constraint_parent_not_filtered(self):
        """Test appending constraint when parent not in filtered versions."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        model.filtered_versions = {}

        model.append_indirect_constraint("child", [200], "parent", 100)

        assert len(model.childs) == 0

    def test_group_versions_single(self):
        """Test grouping single version."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        result = model.group_versions("fastapi", [100], False)

        assert "(= |fastapi| 100)" in result

    def test_group_versions_consecutive(self):
        """Test grouping consecutive versions."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        result = model.group_versions("fastapi", [100, 101, 102], True)

        assert ">=" in result and "<=" in result

    def test_group_versions_non_consecutive(self):
        """Test grouping non-consecutive versions."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        result = model.group_versions("fastapi", [100, 102, 104], True)

        assert "(or" in result

    def test_group_versions_empty(self):
        """Test grouping empty versions."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        result = model.group_versions("fastapi", [], False)

        assert result == ""

    def test_create_constraint_for_group_single(self):
        """Test creating constraint for single version."""
        result = SMTModel.create_constraint_for_group("|pkg|", [100], True)
        assert result == "(= |pkg| 100)"

    def test_create_constraint_for_group_range_ascending(self):
        """Test creating constraint for version range ascending."""
        result = SMTModel.create_constraint_for_group("|pkg|", [100, 101, 102], True)
        assert ">= |pkg| 100" in result
        assert "<= |pkg| 102" in result

    def test_create_constraint_for_group_range_descending(self):
        """Test creating constraint for version range descending."""
        result = SMTModel.create_constraint_for_group("|pkg|", [102, 101, 100], False)
        assert ">= |pkg| 100" in result
        assert "<= |pkg| 102" in result

    # ===== Impact Sum Tests =====

    def test_build_impact_sum_empty(self):
        """Test building impact sum with no impacts."""
        model = SMTModel({"name": "test"}, "PyPIPackage", "mean")
        result = model.build_impact_sum()
        assert result == "0.0"

    def test_build_impact_sum_with_impacts(self, sample_source_data):
        """Test building impact sum with impacts."""
        model = SMTModel(sample_source_data, "PyPIPackage", "mean")
        model.impacts.add("|impact_fastapi|")
        model.impacts.add("|impact_pydantic|")
        result = model.build_impact_sum()

        assert "(+" in result
        assert "impact_fastapi" in result
        assert "impact_pydantic" in result
