import xml.etree.ElementTree as ET
import glob

for f in glob.glob("npc_templates/*.chum5"):
    tree = ET.parse(f)
    root = tree.getroot()
    char = root.find("character")
    if char is not None:
        portrait = char.find("portrait")
        if portrait is not None:
            print(f"Found portrait in {f}: {portrait.text}")
