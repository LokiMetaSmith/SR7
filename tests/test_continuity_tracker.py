import pytest
from scripts.continuity_tracker import add_fact, remove_fact, list_facts, get_db_file, init_db
import tempfile
import os
import json
import sys

# We need to monkeypatch the base path for testing
@pytest.fixture
def mock_db_file(monkeypatch, tmp_path):
    def mock_get_db_file(story_name):
        return os.path.join(str(tmp_path), f"continuity.jsonl")

    monkeypatch.setattr('scripts.continuity_tracker.get_db_file', mock_get_db_file)
    init_db("test_story")
    return mock_get_db_file("test_story")

def test_add_fact(mock_db_file):
    add_fact("test_story", "John", "Appearance", "Has blue eyes")

    with open(mock_db_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["entity"] == "John"
        assert data["fact"] == "Has blue eyes"

def test_remove_fact(mock_db_file):
    add_fact("test_story", "John", "Appearance", "Has blue eyes")
    add_fact("test_story", "John", "Appearance", "Has brown hair")

    remove_fact("test_story", "John", "blue")

    with open(mock_db_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["fact"] == "Has brown hair"

def test_list_facts(mock_db_file, capsys):
    add_fact("test_story", "John", "Appearance", "Has blue eyes")
    list_facts("test_story", "John")

    captured = capsys.readouterr()
    assert "Has blue eyes" in captured.out
