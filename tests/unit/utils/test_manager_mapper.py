"""Unit tests for ManagerNodeTypeMapper."""

from app.schemas.enums import NodeType
from app.utils.manager_node_type_mapper import ManagerNodeTypeMapper


class TestManagerNodeTypeMapper:
    """Test suite for ManagerNodeTypeMapper."""

    def test_pypi_to_node_type(self):
        """Test mapping PyPI manager to node type."""
        result = ManagerNodeTypeMapper.manager_to_node_type("PyPI")
        assert result == NodeType.pypi_package.value

    def test_npm_to_node_type(self):
        """Test mapping NPM manager to node type."""
        result = ManagerNodeTypeMapper.manager_to_node_type("NPM")
        assert result == NodeType.npm_package.value

    def test_maven_to_node_type(self):
        """Test mapping Maven manager to node type."""
        result = ManagerNodeTypeMapper.manager_to_node_type("Maven")
        assert result == NodeType.maven_package.value

    def test_cargo_to_node_type(self):
        """Test mapping Cargo manager to node type."""
        result = ManagerNodeTypeMapper.manager_to_node_type("Cargo")
        assert result == NodeType.cargo_package.value

    def test_rubygems_to_node_type(self):
        """Test mapping RubyGems manager to node type."""
        result = ManagerNodeTypeMapper.manager_to_node_type("RubyGems")
        assert result == NodeType.rubygems_package.value

    def test_nuget_to_node_type(self):
        """Test mapping NuGet manager to node type."""
        result = ManagerNodeTypeMapper.manager_to_node_type("NuGet")
        assert result == NodeType.nuget_package.value

    def test_invalid_manager_defaults_to_pypi(self):
        """Test that invalid manager defaults to PyPI."""
        result = ManagerNodeTypeMapper.manager_to_node_type("InvalidManager")
        assert result == NodeType.pypi_package.value

    def test_case_sensitive_manager(self):
        """Test that manager names are case-sensitive."""
        result = ManagerNodeTypeMapper.manager_to_node_type("pypi")
        # Should default to PyPI since "pypi" (lowercase) is not valid
        assert result == NodeType.pypi_package.value
