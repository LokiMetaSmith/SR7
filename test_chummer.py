import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List

@dataclass
class Contact:
    name: str
    connection: int
    loyalty: int

def test_parse(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    char = root.find("character")
    contacts = []
    contacts_node = char.find("contacts")
    if contacts_node is not None:
        for contact in contacts_node.findall("contact"):
            cn = contact.find("name").text if contact.find("name") is not None else "Unknown Contact"
            cc = int(contact.find("connection").text) if contact.find("connection") is not None else 1
            cl = int(contact.find("loyalty").text) if contact.find("loyalty") is not None else 1
            contacts.append(Contact(name=cn, connection=cc, loyalty=cl))
    print(contacts)

test_parse("npc_templates/Kyber.chum5")
