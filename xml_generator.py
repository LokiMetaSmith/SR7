import argparse
import re
import hashlib
import html
import xml.etree.ElementTree as ET
from xml.dom import minidom
from markdown_it import MarkdownIt

def parse_markdown(text):
    md = MarkdownIt("commonmark").enable("table")
    return md.parse(text)

def escape_xml(text):
    if text is None:
        return ""
    # We can use html.escape but we need to ensure it handles everything correctly
    # xml.etree handles escaping automatically for element text and attributes.
    # We'll just build the ET tree and write it, and it will escape correctly.
    return str(text).strip()

def extract_qualities(tokens):
    qualities = []

    for token in tokens:
        if token.type == "inline":
            # Match formats like **Quality Name** \- 5 Karma (Tag, Tag)
            m = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Karma\s*\((.+?)\)", token.content)
            if m:
                qualities.append((m.group(1), m.group(2), m.group(3)))
                continue

            m2 = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Karma\s*(?:\\|\Z|\n|$)", token.content)
            if m2:
                qualities.append((m2.group(1), m2.group(2), ""))
                continue

            m3 = re.match(r"^\*\*(.+?)\*\*\s*-\s*(.+?)\s*Karma\s*\((.+?)\)", token.content)
            if m3:
                qualities.append((m3.group(1), m3.group(2), m3.group(3)))
                continue

            m4 = re.match(r"^\*\*(.+?)\*\*\s*-\s*(.+?)\s*Karma\s*(?:\\|\Z|\n|$)", token.content)
            if m4:
                qualities.append((m4.group(1), m4.group(2), ""))
                continue

            m5 = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Quality\)", token.content)
            if m5:
                qualities.append((m5.group(1), "0", m5.group(2)))
                continue

    return qualities

def extract_tables(tokens):
    tables = []
    in_table = False
    headers = []
    current_table_rows = []
    current_row = []
    in_cell = False
    cell_content = ""

    for token in tokens:
        if token.type == "table_open":
            in_table = True
            current_table_rows = []
            headers = []
        elif token.type == "table_close":
            in_table = False
            tables.append((headers, current_table_rows))
        elif in_table and token.type == "tr_open":
            current_row = []
        elif in_table and (token.type == "th_open" or token.type == "td_open"):
            in_cell = True
            cell_content = ""
        elif in_table and in_cell and token.type == "inline":
            cell_content += token.content
        elif in_table and (token.type == "th_close" or token.type == "td_close"):
            in_cell = False
            current_row.append(cell_content)
        elif in_table and token.type == "tr_close":
            if not headers:
                headers = [h.replace("**", "").strip() for h in current_row]
            else:
                current_table_rows.append(current_row)
    return tables

def extract_weapons(tables):
    weapons = []

    for headers, rows in tables:
        if "ACC" in headers and "DV" in headers and "AP" in headers:
            acc_idx = headers.index("ACC") if "ACC" in headers else -1
            dv_idx = headers.index("DV") if "DV" in headers else -1
            ap_idx = headers.index("AP") if "AP" in headers else -1
            mode_idx = headers.index("MODE") if "MODE" in headers else -1
            rc_idx = headers.index("RC") if "RC" in headers else -1
            ammo_idx = headers.index("AMMO") if "AMMO" in headers else -1
            avail_idx = headers.index("AVAIL") if "AVAIL" in headers else -1
            cost_idx = headers.index("COST") if "COST" in headers else -1

            if dv_idx == -1 or cost_idx == -1:
                continue

            for row in rows:
                if len(row) > max(dv_idx, cost_idx):
                    name = row[0].replace("**", "").strip()
                    dv = row[dv_idx].strip()
                    cost = row[cost_idx].strip()

                    if dv and cost and dv != "–" and cost != "–":
                        weapon = {
                            "name": name,
                            "acc": row[acc_idx].strip() if acc_idx != -1 and len(row) > acc_idx else "",
                            "dv": dv,
                            "ap": row[ap_idx].strip() if ap_idx != -1 and len(row) > ap_idx else "",
                            "mode": row[mode_idx].strip() if mode_idx != -1 and len(row) > mode_idx else "",
                            "rc": row[rc_idx].strip() if rc_idx != -1 and len(row) > rc_idx else "",
                            "ammo": row[ammo_idx].strip() if ammo_idx != -1 and len(row) > ammo_idx else "",
                            "avail": row[avail_idx].strip() if avail_idx != -1 and len(row) > avail_idx else "",
                            "cost": cost
                        }
                        weapons.append(weapon)
    return weapons

def generate_qualities_xml(qualities, output_path):
    root = ET.Element("chummer")
    qualities_node = ET.SubElement(root, "qualities")

    for name, cost, tags in qualities:
        q_node = ET.SubElement(qualities_node, "quality")
        hash_id = hashlib.md5(name.encode('utf-8')).hexdigest()
        ET.SubElement(q_node, "id").text = f"CUSTOM_QUAL_{hash_id}"
        ET.SubElement(q_node, "name").text = name
        ET.SubElement(q_node, "bp").text = str(cost)

        # Tags could map to categories or tags in Chummer XML
        if tags:
            ET.SubElement(q_node, "tags").text = tags

    # Pretty print
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xmlstr)
    print(f"Generated {output_path} with {len(qualities)} qualities.")

def generate_weapons_xml(weapons, output_path):
    root = ET.Element("chummer")
    weapons_node = ET.SubElement(root, "weapons")

    for w in weapons:
        w_node = ET.SubElement(weapons_node, "weapon")
        hash_id = hashlib.md5(w['name'].encode('utf-8')).hexdigest()
        ET.SubElement(w_node, "id").text = f"CUSTOM_WEAP_{hash_id}"
        ET.SubElement(w_node, "name").text = w['name']
        ET.SubElement(w_node, "accuracy").text = w['acc']
        ET.SubElement(w_node, "damage").text = w['dv']
        ET.SubElement(w_node, "ap").text = w['ap']
        ET.SubElement(w_node, "mode").text = w['mode']
        ET.SubElement(w_node, "rc").text = w['rc']
        ET.SubElement(w_node, "ammo").text = w['ammo']
        ET.SubElement(w_node, "avail").text = w['avail']
        ET.SubElement(w_node, "cost").text = w['cost']

    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xmlstr)
    print(f"Generated {output_path} with {len(weapons)} weapons.")

def main():
    parser = argparse.ArgumentParser(description="Generate Chummer XML files from Markdown.")
    parser.add_argument("file", nargs="?", default="Fan made Shadowrun 7th Edition rules.md")
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = parse_markdown(text)

    qualities = extract_qualities(tokens)
    generate_qualities_xml(qualities, "custom_sr7e_qualities.xml")

    tables = extract_tables(tokens)
    weapons = extract_weapons(tables)
    generate_weapons_xml(weapons, "custom_sr7e_weapons.xml")

if __name__ == "__main__":
    main()
