"""
Text processing utilities.
"""

import re
import unicodedata
from typing import Optional


def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert text to URL-safe slug.

    Args:
        text: Text to slugify
        max_length: Maximum slug length

    Returns:
        URL-safe slug

    Example:
        >>> slugify("Hello World!")
        "hello-world"
    """
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)

    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)

    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)

    # Strip leading/trailing hyphens
    text = text.strip("-")

    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]

    return text


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to max length, preserving word boundaries.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    # Account for suffix
    max_text = max_length - len(suffix)

    if max_text <= 0:
        return suffix[:max_length]

    # Find word boundary
    truncated = text[:max_text]
    last_space = truncated.rfind(" ")

    if last_space > max_text // 2:
        truncated = truncated[:last_space]

    return truncated.rstrip() + suffix


def word_count(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Text to count

    Returns:
        Word count
    """
    return len(text.split())


def reading_time_minutes(text: str, wpm: int = 200) -> int:
    """
    Estimate reading time in minutes.

    Args:
        text: Text to estimate
        wpm: Words per minute (default 200)

    Returns:
        Reading time in minutes (minimum 1)
    """
    words = word_count(text)
    minutes = max(1, round(words / wpm))
    return minutes


def extract_sentences(text: str, max_sentences: int = 3) -> list[str]:
    """
    Extract first N sentences from text.

    Args:
        text: Text to extract from
        max_sentences: Maximum sentences

    Returns:
        List of sentences
    """
    # Simple sentence splitting
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = re.split(sentence_pattern, text.strip())

    result = []
    for sentence in sentences[:max_sentences]:
        sentence = sentence.strip()
        if sentence:
            result.append(sentence)

    return result


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: HTML text

    Returns:
        Clean text
    """
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Decode common entities
    clean = clean.replace("&nbsp;", " ")
    clean = clean.replace("&amp;", "&")
    clean = clean.replace("&lt;", "<")
    clean = clean.replace("&gt;", ">")
    clean = clean.replace("&quot;", '"')
    # Collapse whitespace
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def highlight_matches(
    text: str,
    terms: list[str],
    before: str = "**",
    after: str = "**",
) -> str:
    """
    Highlight search terms in text.

    Args:
        text: Text to highlight in
        terms: Terms to highlight
        before: String to insert before match
        after: String to insert after match

    Returns:
        Text with highlights
    """
    result = text
    for term in terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub(f"{before}\\g<0>{after}", result)
    return result


def generate_excerpt(
    text: str,
    query: Optional[str] = None,
    length: int = 200,
) -> str:
    """
    Generate an excerpt from text, optionally centered on query.

    Args:
        text: Full text
        query: Optional query to center on
        length: Target excerpt length

    Returns:
        Excerpt string
    """
    if len(text) <= length:
        return text

    if query:
        # Find query position
        query_lower = query.lower()
        text_lower = text.lower()
        pos = text_lower.find(query_lower)

        if pos >= 0:
            # Center around query
            half = length // 2
            start = max(0, pos - half)
            end = min(len(text), pos + len(query) + half)

            excerpt = text[start:end]

            if start > 0:
                excerpt = "..." + excerpt
            if end < len(text):
                excerpt = excerpt + "..."

            return excerpt

    # Default: take from beginning
    return truncate(text, length)

