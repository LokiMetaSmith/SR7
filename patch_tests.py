import sys

filename = "tests/test_ui.py"
with open(filename, 'r') as f:
    content = f.read()

replacement = """import os
@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    # Initialize pygame for headless testing
"""
content = content.replace('@pytest.fixture(scope="module", autouse=True)\ndef setup_pygame():\n    # Initialize pygame for headless testing\n', replacement)

with open(filename, 'w') as f:
    f.write(content)
