import pytest
import sys
import unittest.mock as mock

# Mock the openai import before importing generate_novella
sys.modules['openai'] = mock.MagicMock()

from scripts.generate_novella import parse_outline, generate_chapter

def test_parse_outline():
    outline_text = """
# Outline
*   **Chapter 1: The Beginning** - Stuff happens.
*   **Chapter 2: The Middle** - More stuff happens.
    * Details
*   **Chapter 3: The End** - It ends.
"""
    chapters = parse_outline(outline_text)
    assert len(chapters) == 3
    assert chapters[0] == "Chapter 1: The Beginning** - Stuff happens."
    assert chapters[1] == "Chapter 2: The Middle** - More stuff happens."
    assert chapters[2] == "Chapter 3: The End** - It ends."

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockCompletions:
    def create(self, **kwargs):
        return MockResponse("This is a generated chapter.")

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockClient:
    def __init__(self):
        self.chat = MockChat()

def test_generate_chapter():
    client = MockClient()
    result = generate_chapter(client, "Test prompt", "Previous context")
    assert result == "This is a generated chapter."
