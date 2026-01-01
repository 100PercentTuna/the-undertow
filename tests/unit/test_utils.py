"""
Tests for utility functions.
"""

import pytest

from undertow.utils.text import (
    slugify,
    truncate,
    word_count,
    reading_time_minutes,
    extract_sentences,
    clean_html,
    highlight_matches,
    generate_excerpt,
)


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_text(self) -> None:
        """Test basic text slugification."""
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self) -> None:
        """Test handling of special characters."""
        assert slugify("Hello, World!") == "hello-world"

    def test_unicode(self) -> None:
        """Test unicode handling."""
        assert slugify("Café Résumé") == "cafe-resume"

    def test_multiple_spaces(self) -> None:
        """Test handling of multiple spaces."""
        assert slugify("Hello   World") == "hello-world"

    def test_max_length(self) -> None:
        """Test max length truncation."""
        result = slugify("This is a very long title", max_length=10)
        assert len(result) <= 10


class TestTruncate:
    """Tests for truncate function."""

    def test_no_truncation_needed(self) -> None:
        """Test text shorter than max."""
        assert truncate("Hello", 10) == "Hello"

    def test_truncation_at_word_boundary(self) -> None:
        """Test truncation preserves words."""
        result = truncate("Hello World Test", 12)
        assert result == "Hello..."

    def test_custom_suffix(self) -> None:
        """Test custom suffix."""
        result = truncate("Hello World", 8, suffix="…")
        assert result.endswith("…")


class TestWordCount:
    """Tests for word_count function."""

    def test_basic_count(self) -> None:
        """Test basic word counting."""
        assert word_count("Hello World") == 2

    def test_empty_string(self) -> None:
        """Test empty string."""
        assert word_count("") == 1  # split returns ['']

    def test_multiline(self) -> None:
        """Test multiline text."""
        assert word_count("Hello\nWorld\nTest") == 3


class TestReadingTime:
    """Tests for reading_time_minutes function."""

    def test_minimum_one_minute(self) -> None:
        """Test minimum is 1 minute."""
        assert reading_time_minutes("Hello") == 1

    def test_longer_text(self) -> None:
        """Test longer text calculation."""
        text = " ".join(["word"] * 400)  # 400 words
        assert reading_time_minutes(text) == 2


class TestExtractSentences:
    """Tests for extract_sentences function."""

    def test_basic_extraction(self) -> None:
        """Test basic sentence extraction."""
        text = "First sentence. Second sentence. Third sentence."
        result = extract_sentences(text, 2)
        assert len(result) == 2
        assert result[0] == "First sentence."

    def test_different_punctuation(self) -> None:
        """Test handling of different punctuation."""
        text = "Question? Exclamation! Statement."
        result = extract_sentences(text, 3)
        assert len(result) == 3


class TestCleanHtml:
    """Tests for clean_html function."""

    def test_removes_tags(self) -> None:
        """Test HTML tag removal."""
        assert clean_html("<p>Hello</p>") == "Hello"

    def test_decodes_entities(self) -> None:
        """Test entity decoding."""
        assert clean_html("Hello&amp;World") == "Hello&World"

    def test_collapses_whitespace(self) -> None:
        """Test whitespace collapsing."""
        assert clean_html("Hello   World") == "Hello World"


class TestHighlightMatches:
    """Tests for highlight_matches function."""

    def test_basic_highlight(self) -> None:
        """Test basic highlighting."""
        result = highlight_matches("Hello World", ["World"])
        assert result == "Hello **World**"

    def test_case_insensitive(self) -> None:
        """Test case insensitive matching."""
        result = highlight_matches("Hello world", ["WORLD"])
        assert "**world**" in result

    def test_custom_markers(self) -> None:
        """Test custom highlight markers."""
        result = highlight_matches("Hello World", ["World"], "<b>", "</b>")
        assert result == "Hello <b>World</b>"


class TestGenerateExcerpt:
    """Tests for generate_excerpt function."""

    def test_short_text(self) -> None:
        """Test text shorter than length."""
        assert generate_excerpt("Hello", length=100) == "Hello"

    def test_no_query(self) -> None:
        """Test excerpt without query."""
        text = "A" * 300
        result = generate_excerpt(text, length=100)
        assert len(result) <= 103  # Includes "..."

    def test_with_query(self) -> None:
        """Test excerpt centered on query."""
        text = "Start " + "x" * 100 + " TARGET " + "y" * 100 + " End"
        result = generate_excerpt(text, query="TARGET", length=50)
        assert "TARGET" in result

