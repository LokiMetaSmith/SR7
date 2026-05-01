import pytest
import pygame
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.components import MapGrid

@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((100, 100), pygame.HIDDEN)
    yield
    pygame.quit()

def test_mapgrid_blast():
    layout = ["###", "#T#", "###"]
    legend = {"#": "Wall", "T": "Target Zone"}
    mg = MapGrid(layout, legend)
    mg.blast_zones.append("Target")

    # Render it
    surface = pygame.Surface((800, 600))
    mg.draw(surface, 0, 0)

    # We just ensure it runs without crashing, visual logic is mostly drawing logic.
    assert "Target" in mg.blast_zones
