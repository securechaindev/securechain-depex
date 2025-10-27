"""Unit tests for PomXmlAnalyzer."""
import pytest
from unittest.mock import mock_open, patch

from app.domain.repo_analyzer.requirement_files.pom_xml_analyzer import PomXmlAnalyzer


class TestPomXmlAnalyzer:
    """Test suite for PomXmlAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a PomXmlAnalyzer instance."""
        return PomXmlAnalyzer()

    def test_init(self, analyzer):
        """Test PomXmlAnalyzer initialization."""
        assert analyzer.manager == "Maven"

    def test_parse_file_with_dependencies(self, analyzer):
        """Test parsing a valid pom.xml with dependencies."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>3.0.2</version>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <version>42.5.1</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        assert result == {
            "org.springframework.boot:spring-boot-starter-web": "[3.0.2]",
            "org.postgresql:postgresql": "[42.5.1]"
        }

    def test_parse_file_no_dependencies(self, analyzer):
        """Test parsing a pom.xml without dependencies."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        assert result == {}

    def test_parse_file_empty_dependencies(self, analyzer):
        """Test parsing a pom.xml with empty dependencies section."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        assert result == {}

    def test_parse_file_single_dependency(self, analyzer):
        """Test parsing a pom.xml with a single dependency."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        assert result == {"junit:junit": "[4.13.2]"}

    def test_parse_file_missing_version(self, analyzer):
        """Test parsing when a dependency is missing version."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>no-version</artifactId>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>with-version</artifactId>
            <version>1.0.0</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        assert result == {
            "com.example:no-version": "any",
            "com.example:with-version": "[1.0.0]"
        }

    def test_parse_file_missing_group_id(self, analyzer):
        """Test parsing when a dependency is missing groupId."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <artifactId>no-group</artifactId>
            <version>1.0.0</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>with-group</artifactId>
            <version>2.0.0</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        # Dependency without groupId should be skipped
        assert result == {"com.example:with-group": "[2.0.0]"}

    def test_parse_file_missing_artifact_id(self, analyzer):
        """Test parsing when a dependency is missing artifactId."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>com.example</groupId>
            <version>1.0.0</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>with-artifact</artifactId>
            <version>2.0.0</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        # Dependency without artifactId should be skipped
        assert result == {"com.example:with-artifact": "[2.0.0]"}

    def test_parse_file_with_properties(self, analyzer):
        """Test parsing with property placeholders."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <properties>
        <spring.version>3.0.2</spring.version>
        <junit.version>5.9.1</junit.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
            <version>${spring.version}</version>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${junit.version}</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        assert result == {
            "org.springframework.boot:spring-boot-starter": "[3.0.2]",
            "org.junit.jupiter:junit-jupiter": "[5.9.1]"
        }

    def test_parse_file_with_undefined_property(self, analyzer):
        """Test parsing with undefined property placeholder."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <properties>
        <spring.version>3.0.2</spring.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>my-lib</artifactId>
            <version>${undefined.property}</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        # Undefined property should default to "any"
        assert result == {"com.example:my-lib": "any"}

    def test_parse_file_with_range_versions(self, analyzer):
        """Test parsing versions with Maven range syntax."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>range1</artifactId>
            <version>[1.0,2.0)</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>range2</artifactId>
            <version>(,1.0]</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>range3</artifactId>
            <version>[1.0,)</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        # Versions with range syntax should be kept as-is
        assert result == {
            "com.example:range1": "[1.0,2.0)",
            "com.example:range2": "(,1.0]",
            "com.example:range3": "[1.0,)"
        }

    def test_parse_file_mixed_versions(self, analyzer):
        """Test parsing with mixed version formats."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <properties>
        <prop.version>2.0.0</prop.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>standard</artifactId>
            <version>1.0.0</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>with-property</artifactId>
            <version>${prop.version}</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>range</artifactId>
            <version>[3.0,4.0)</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>no-version</artifactId>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        assert result == {
            "com.example:standard": "[1.0.0]",
            "com.example:with-property": "[2.0.0]",
            "com.example:range": "[3.0,4.0)",
            "com.example:no-version": "any"
        }

    def test_parse_file_empty_group_or_artifact(self, analyzer):
        """Test parsing with empty groupId or artifactId elements."""
        pom_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId></groupId>
            <artifactId>empty-group</artifactId>
            <version>1.0.0</version>
        </dependency>
        <dependency>
            <groupId>com.example</groupId>
            <artifactId></artifactId>
            <version>2.0.0</version>
        </dependency>
    </dependencies>
</project>
"""
        with patch("builtins.open", mock_open(read_data=pom_xml_content)):
            result = analyzer._parse_file("/fake/path", "pom.xml")

        # Empty strings should still create keys
        assert result == {
            ":empty-group": "[1.0.0]",
            "com.example:": "[2.0.0]"
        }
