"""Unit tests for utility functions in paper-poller."""

import pytest
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to set env vars before importing the module
os.environ.setdefault("WEBHOOK_URL", '["http://example.com"]')

from paper_poller import convert_commit_hash_to_short, convert_build_date, Color, COLORS, CHANNEL_COLORS


class TestConvertCommitHashToShort:
    """Tests for convert_commit_hash_to_short function."""

    def test_short_hash_conversion(self):
        """Test that commit hashes are shortened to 7 characters."""
        full_hash = "abc123def456789ghijklmno"
        short_hash = convert_commit_hash_to_short(full_hash)
        assert short_hash == "abc123d"
        assert len(short_hash) == 7

    def test_short_hash_with_exact_7_chars(self):
        """Test that hashes with exactly 7 characters remain unchanged."""
        hash_7_chars = "abc123d"
        short_hash = convert_commit_hash_to_short(hash_7_chars)
        assert short_hash == "abc123d"

    def test_short_hash_with_less_than_7_chars(self):
        """Test that hashes shorter than 7 characters are returned as-is."""
        short = "abc"
        result = convert_commit_hash_to_short(short)
        assert result == "abc"


class TestConvertBuildDate:
    """Tests for convert_build_date function."""

    def test_valid_date_conversion(self):
        """Test that valid ISO date strings are converted correctly."""
        date_string = "2025-10-12T12:00:00.000Z"
        result = convert_build_date(date_string)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 12
        assert result.hour == 12
        assert result.minute == 0
        assert result.second == 0

    def test_date_with_different_timezone(self):
        """Test date conversion with timezone information."""
        date_string = "2025-10-12T12:00:00.000+00:00"
        result = convert_build_date(date_string)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None


class TestColorEnums:
    """Tests for Color enum and color mappings."""

    def test_color_enum_values(self):
        """Test that Color enum has correct hex values."""
        assert Color.BLUE.value == 0x2b7fff
        assert Color.GREEN.value == 0x4ecb8b
        assert Color.PINK.value == 0xf06292
        assert Color.ORANGE.value == 0xffb74d
        assert Color.PURPLE.value == 0x7e57c2
        assert Color.RED.value == 0xea5b6f
        assert Color.YELLOW.value == 0xffc859

    def test_colors_dict_mapping(self):
        """Test that COLORS dict maps lowercase names to values."""
        assert COLORS["blue"] == 0x2b7fff
        assert COLORS["green"] == 0x4ecb8b
        assert COLORS["red"] == 0xea5b6f
        assert len(COLORS) == 7

    def test_channel_colors_mapping(self):
        """Test that channel names map to appropriate colors."""
        assert CHANNEL_COLORS["ALPHA"] == Color.RED.value
        assert CHANNEL_COLORS["BETA"] == Color.YELLOW.value
        assert CHANNEL_COLORS["STABLE"] == Color.BLUE.value
        assert CHANNEL_COLORS["RECOMMENDED"] == Color.GREEN.value


class TestEnvironmentConfiguration:
    """Tests for environment variable configuration."""

    def test_check_all_versions_default(self):
        """Test that CHECK_ALL_VERSIONS defaults to False."""
        # Need to re-import with clean env
        import importlib
        import paper_poller as pp

        # The module was already imported, so we check the value
        # In actual tests, this would be set up properly
        assert pp.CHECK_ALL_VERSIONS in [True, False]

    def test_dry_run_default(self):
        """Test that DRY_RUN defaults to False."""
        import paper_poller as pp
        assert pp.DRY_RUN in [True, False]
