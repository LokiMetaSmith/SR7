import pytest
from scripts.llm_smell_linter import check_file
import tempfile
import os

def run_linter_on_content(content):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w", encoding="utf-8") as f:
        f.write(content)
        temp_path = f.name

    try:
        results = check_file(temp_path)
    finally:
        os.remove(temp_path)
    return results

def test_x_is_the_y_of_z():
    content = "The crystal is the heart of the machine."
    results = run_linter_on_content(content)
    assert any(smell == "x_is_the_y_of_z" for _, smell, _, _ in results)

def test_not_just_x_its_y():
    content = "It was not merely survival, but also a testament to human will."
    results = run_linter_on_content(content)
    assert any(smell == "not_just_x_its_y" for _, smell, _, _ in results)

def test_excessive_em_dashes():
    content = "The silence---a heavy, oppressive silence---filled the room---and choked them."
    results = run_linter_on_content(content)
    assert any(smell == "excessive_em_dashes" for _, smell, _, _ in results)

def test_repetitive_openings():
    content = "The next morning, everything changed."
    results = run_linter_on_content(content)
    assert any(smell == "repetitive_openings" for _, smell, _, _ in results)

def test_consecutive_short_sentences():
    content = "The sky was dark. It was raining. He ran fast."
    results = run_linter_on_content(content)
    assert any(smell == "consecutive_short_sentences" for _, smell, _, _ in results)

def test_llm_buzzwords():
    content = "We must navigate this multifaceted tapestry."
    results = run_linter_on_content(content)
    assert any(smell == "llm_buzzwords" for _, smell, _, _ in results)

def test_lexical_repetition():
    content = "The bright blue light. The bright blue light shone brightly. The bright blue light blinded him."
    results = run_linter_on_content(content)
    assert any(smell == "lexical_repetition" for _, smell, _, _ in results)

def test_punchline_ending():
    content = "The Black Titan fell to its knees, the massive structure shaking the ground, the very earth trembling beneath its unbelievable and monumental weight. It was an earth-shattering event that changed everything forever and nobody would forget it. And so it ended."
    results = run_linter_on_content(content)
    assert any(smell == "punchline_ending" for _, smell, _, _ in results)
