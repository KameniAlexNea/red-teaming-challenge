"""Tests for utility functions."""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from alex_red_teaming.utils import (
    create_output_dir,
    save_json,
    parse_analysis_response,
)


class TestCreateOutputDir(unittest.TestCase):
    """Test the create_output_dir function."""

    def test_create_output_dir_creates_directories(self):
        """Test that create_output_dir creates the expected directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = create_output_dir(temp_dir)

            # Check that the main directory was created
            self.assertTrue(result_dir.exists())
            self.assertTrue(result_dir.is_dir())

            # Check that subdirectories were created
            self.assertTrue((result_dir / "vulnerabilities").exists())
            self.assertTrue((result_dir / "conversations").exists())
            self.assertTrue((result_dir / "logs").exists())

            # Check that the directory name contains timestamp
            self.assertTrue(result_dir.name.startswith("red_teaming_"))

    def test_create_output_dir_returns_path(self):
        """Test that create_output_dir returns a Path object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = create_output_dir(temp_dir)
            self.assertIsInstance(result_dir, Path)


class TestSaveJson(unittest.TestCase):
    """Test the save_json function."""

    def test_save_json_writes_file(self):
        """Test that save_json writes data to file correctly."""
        test_data = {"test": "value", "number": 42, "list": [1, 2, 3]}

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            save_json(test_data, temp_path)

            # Read the file back and verify content
            with open(temp_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data, test_data)
        finally:
            temp_path.unlink()

    def test_save_json_handles_unicode(self):
        """Test that save_json handles unicode characters correctly."""
        test_data = {"unicode": "测试数据", "emoji": "🔥", "special": "café"}

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            save_json(test_data, temp_path)

            with open(temp_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data, test_data)
        finally:
            temp_path.unlink()

    @patch("alex_red_teaming.utils.logger")
    def test_save_json_logs_error_on_failure(self, mock_logger):
        """Test that save_json logs an error when file writing fails."""
        test_data = {"test": "value"}
        invalid_path = Path("/invalid/path/file.json")

        save_json(test_data, invalid_path)

        mock_logger.error.assert_called_once()
        self.assertIn("Error saving JSON", mock_logger.error.call_args[0][0])


class TestParseAnalysisResponse(unittest.TestCase):
    """Test the parse_analysis_response function."""

    def test_parse_json_format_success(self):
        """Test parsing a well-formed JSON analysis response."""
        analysis = """
        {
            "VULNERABILITY_FOUND": "Yes",
            "SEVERITY": "high",
            "EXPLANATION": "Model revealed sensitive information",
            "EVIDENCE": "The model disclosed internal training data",
            "CONFIDENCE": 8
        }
        """

        result, _ = parse_analysis_response(analysis)

        self.assertTrue(result["vulnerability_found"])
        self.assertEqual(result["severity"], "high")
        self.assertEqual(result["explanation"], "Model revealed sensitive information")
        self.assertEqual(
            result["evidence"], "The model disclosed internal training data"
        )
        self.assertEqual(result["confidence"], 8)
        self.assertEqual(result["raw_analysis"], analysis)

    def test_parse_json_format_no_vulnerability(self):
        """Test parsing JSON response with no vulnerability found."""
        analysis = """
        {
            "VULNERABILITY_FOUND": "No",
            "SEVERITY": null,
            "EXPLANATION": "Response appears safe",
            "EVIDENCE": "No harmful content detected",
            "CONFIDENCE": 9
        }
        """

        result, _ = parse_analysis_response(analysis)

        self.assertFalse(result["vulnerability_found"])
        self.assertIsNone(result["severity"])
        self.assertEqual(result["explanation"], "Response appears safe")
        self.assertEqual(result["evidence"], "No harmful content detected")
        self.assertEqual(result["confidence"], 9)

    def test_parse_line_format_success(self):
        """Test parsing line-by-line format analysis response."""
        analysis = """
        VULNERABILITY_FOUND: Yes
        SEVERITY: critical
        EXPLANATION: Model generated harmful content
        EVIDENCE: Output contained explicit instructions for illegal activities
        CONFIDENCE: 10
        """

        result, _ = parse_analysis_response(analysis)

        self.assertTrue(result["vulnerability_found"])
        self.assertEqual(result["severity"], "critical")
        self.assertEqual(result["explanation"], "Model generated harmful content")
        self.assertEqual(
            result["evidence"],
            "Output contained explicit instructions for illegal activities",
        )
        self.assertEqual(result["confidence"], 10)

    def test_parse_line_format_no_vulnerability(self):
        """Test parsing line format with no vulnerability."""
        analysis = """
        VULNERABILITY_FOUND: No
        SEVERITY: 
        EXPLANATION: Safe response detected
        EVIDENCE: Model refused to comply with harmful request
        CONFIDENCE: 7
        """

        result, _ = parse_analysis_response(analysis)

        self.assertFalse(result["vulnerability_found"])
        self.assertIsNone(result["severity"])  # Empty string, not None for line format
        self.assertEqual(result["explanation"], "Safe response detected")
        self.assertEqual(
            result["evidence"], "Model refused to comply with harmful request"
        )
        self.assertEqual(result["confidence"], 7)

    def test_parse_mixed_case_vulnerability_found(self):
        """Test parsing with different case variations of 'yes'."""
        test_cases = [
            "VULNERABILITY_FOUND: YES",
            "VULNERABILITY_FOUND: yes",
            "VULNERABILITY_FOUND: Yes",
            "VULNERABILITY_FOUND: YeS",
        ]

        for analysis in test_cases:
            with self.subTest(analysis=analysis):
                result, _ = parse_analysis_response(analysis)
                self.assertTrue(result["vulnerability_found"])

    def test_parse_severity_levels(self):
        """Test parsing different severity levels."""
        severity_levels = ["low", "medium", "high", "critical"]

        for severity in severity_levels:
            analysis = f"SEVERITY: {severity}"
            with self.subTest(severity=severity):
                result, _ = parse_analysis_response(analysis)
                self.assertEqual(result["severity"], severity)

    def test_parse_invalid_severity_ignored(self):
        """Test that invalid severity levels are ignored."""
        analysis = "SEVERITY: invalid_level"
        result, _ = parse_analysis_response(analysis)
        self.assertIsNone(result["severity"])

    def test_parse_confidence_extraction(self):
        """Test confidence score extraction from various formats."""
        test_cases = [
            ("CONFIDENCE: 8", 8),
            ("CONFIDENCE: 10 out of 10", 10),
            ("CONFIDENCE: 5/10", 0),
            ("CONFIDENCE: 7.5", 7.5),  # Should parse as int
            ("CONFIDENCE: invalid", 0),  # Should default to 0
        ]

        for analysis, expected in test_cases:
            with self.subTest(analysis=analysis):
                result, _ = parse_analysis_response(analysis)
                self.assertEqual(result["confidence"], expected)

    def test_parse_malformed_json_fallback(self):
        """Test that malformed JSON falls back to line parsing."""
        analysis = """
        {
            "VULNERABILITY_FOUND": "Yes",
            "SEVERITY": "high"
            // This is malformed JSON
        EXPLANATION: Fallback parsing should work
        CONFIDENCE: 6
        """

        result, _ = parse_analysis_response(analysis)

        # Should fall back to line parsing
        self.assertEqual(result["explanation"], "Fallback parsing should work")
        self.assertEqual(result["confidence"], 6)

    def test_parse_empty_analysis(self):
        """Test parsing empty or whitespace-only analysis."""
        result, _ = parse_analysis_response("")

        self.assertFalse(result["vulnerability_found"])
        self.assertIsNone(result["severity"])
        self.assertEqual(result["explanation"], "Parsing failed")
        self.assertEqual(result["evidence"], "")
        self.assertEqual(result["confidence"], 0)
        self.assertEqual(result["raw_analysis"], "")

    def test_parse_partial_analysis(self):
        """Test parsing analysis with only some fields present."""
        analysis = """
        VULNERABILITY_FOUND: Yes
        EXPLANATION: Partial analysis
        """

        result, _ = parse_analysis_response(analysis)

        self.assertTrue(result["vulnerability_found"])
        self.assertIsNone(result["severity"])  # Not provided
        self.assertEqual(result["explanation"], "Partial analysis")
        self.assertEqual(result["evidence"], "")  # Not provided
        self.assertEqual(result["confidence"], 0)  # Not provided

    def test_parse_multiline_explanation(self):
        """Test parsing explanation that spans multiple lines."""
        analysis = """
        VULNERABILITY_FOUND: Yes
        EXPLANATION: This is a multi-line explanation
        EVIDENCE: Multiple lines of evidence here
        CONFIDENCE: 8
        """

        result, _ = parse_analysis_response(analysis)

        self.assertTrue(result["vulnerability_found"])
        self.assertEqual(result["explanation"], "This is a multi-line explanation")
        self.assertEqual(result["evidence"], "Multiple lines of evidence here")
        self.assertEqual(result["confidence"], 8)

    def test_parse_json_with_missing_fields(self):
        """Test parsing JSON with some missing fields."""
        analysis = """
        {
            "VULNERABILITY_FOUND": "Yes",
            "EXPLANATION": "Only some fields present"
        }
        """

        result, _ = parse_analysis_response(analysis)

        self.assertTrue(result["vulnerability_found"])
        self.assertIsNone(result["severity"])
        self.assertEqual(result["explanation"], "Only some fields present")
        self.assertEqual(result["evidence"], "")
        self.assertEqual(result["confidence"], 0)

    def test_parse_preserves_raw_analysis(self):
        """Test that raw analysis is always preserved."""
        original_analysis = "Some random text that doesn't match any format"
        result, _ = parse_analysis_response(original_analysis)

        self.assertEqual(result["raw_analysis"], original_analysis)

    def test_parse_case_insensitive_vulnerability_detection(self):
        """Test that vulnerability detection is case insensitive."""
        test_cases = [
            "VULNERABILITY_FOUND: yes",
            "vulnerability_found: YES",
            "Vulnerability_Found: Yes",
            "VULNERABILITY_FOUND: this contains yes in the text",
        ]

        for analysis in test_cases:
            with self.subTest(analysis=analysis):
                result, _ = parse_analysis_response(analysis)
                self.assertTrue(result["vulnerability_found"])

    def test_parse_case_insensitive_field_names(self):
        """Test that all field names are case insensitive."""
        analysis = """
        vulnerability_found: Yes
        severity: high
        explanation: Case insensitive test
        evidence: Field names in lowercase
        confidence: 9
        """

        result, _ = parse_analysis_response(analysis)

        self.assertTrue(result["vulnerability_found"])
        self.assertEqual(result["severity"], "high")
        self.assertEqual(result["explanation"], "Case insensitive test")
        self.assertEqual(result["evidence"], "Field names in lowercase")
        self.assertEqual(result["confidence"], 9)

    def test_parse_special_characters_in_content(self):
        """Test parsing with special characters in content."""
        analysis = """
        VULNERABILITY_FOUND: Yes
        EXPLANATION: Contains special chars: @#$%^&*()
        EVIDENCE: Unicode: café, émojis: 🔥💻, quotes: "test"
        CONFIDENCE: 5
        """

        result, _ = parse_analysis_response(analysis)

        self.assertTrue(result["vulnerability_found"])
        self.assertEqual(result["explanation"], "Contains special chars: @#$%^&*()")
        self.assertEqual(
            result["evidence"], 'Unicode: café, émojis: 🔥💻, quotes: "test"'
        )
        self.assertEqual(result["confidence"], 5)


if __name__ == "__main__":
    unittest.main()
