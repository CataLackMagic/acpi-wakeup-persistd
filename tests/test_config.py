import unittest
import os
import tempfile
import sys
import logging

# Ensure we can import the source
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from config_parser import parse_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL) # Suppress logs for cleaner test output

class TestConfigParser(unittest.TestCase):

    def test_parse_config_with_both_sections(self):
        """Test parsing a config file with both enabled and disabled sections."""
        config_content = """
[enabled]
USB0
XHCI

[disabled]
LPC
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            enabled, disabled = parse_config(config_path)
            self.assertEqual(enabled, {'USB0', 'XHCI'})
            self.assertEqual(disabled, {'LPC'})
        finally:
            os.unlink(config_path)

    def test_parse_config_with_only_enabled(self):
        """Test parsing a config file with only enabled section."""
        config_content = """
[enabled]
USB0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            enabled, disabled = parse_config(config_path)
            self.assertEqual(enabled, {'USB0'})
            self.assertEqual(disabled, set())
        finally:
            os.unlink(config_path)

    def test_parse_config_with_comments_and_blanks(self):
        """Test parsing a config file with comments and blank lines."""
        config_content = """
# This is a comment
[enabled]

USB0  # Inline comment
XHCI

[disabled]
LPC
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            enabled, disabled = parse_config(config_path)
            self.assertEqual(enabled, {'USB0', 'XHCI'})
            self.assertEqual(disabled, {'LPC'})
        finally:
            os.unlink(config_path)

    def test_parse_config_missing_file(self):
        """Test that FileNotFoundError is raised for missing config file."""
        with self.assertRaises(FileNotFoundError):
            parse_config('/nonexistent/config.conf')

    def test_parse_config_case_insensitivity(self):
        """Test that section names are case insensitive."""
        config_content = """
[Enabled]
USB0

[DISABLED]
LPC
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            enabled, disabled = parse_config(config_path)
            self.assertEqual(enabled, {'USB0'})
            self.assertEqual(disabled, {'LPC'})
        finally:
            os.unlink(config_path)


if __name__ == '__main__':
    unittest.main()
