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
    try:
        tree = ET.parse(output_path)
        root = tree.getroot()
        qualities_node = root.find("qualities")
        if qualities_node is None:
            qualities_node = ET.SubElement(root, "qualities")
    except FileNotFoundError:
        root = ET.Element("chummer")
        qualities_node = ET.SubElement(root, "qualities")

    existing_qualities = {q.find("name").text: q for q in qualities_node.findall("quality") if q.find("name") is not None}

    added_count = 0
    updated_count = 0

    for name, cost, tags in qualities:
        if name in existing_qualities:
            q_node = existing_qualities[name]
            bp_node = q_node.find("bp")
            if bp_node is not None:
                bp_node.text = str(cost)
            else:
                ET.SubElement(q_node, "bp").text = str(cost)

            if tags:
                tags_node = q_node.find("tags")
                if tags_node is not None:
                    tags_node.text = tags
                else:
                    ET.SubElement(q_node, "tags").text = tags
            updated_count += 1
        else:
            q_node = ET.SubElement(qualities_node, "quality")
            hash_id = hashlib.md5(name.encode('utf-8')).hexdigest()
            ET.SubElement(q_node, "id").text = f"CUSTOM_QUAL_{hash_id}"
            ET.SubElement(q_node, "name").text = name
            ET.SubElement(q_node, "bp").text = str(cost)
            if tags:
                ET.SubElement(q_node, "tags").text = tags
            added_count += 1

    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    # Clean up extra newlines generated by minidom
    xmlstr = '\n'.join([line for line in xmlstr.split('\n') if line.strip()])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xmlstr)
    print(f"Updated {output_path}: {added_count} added, {updated_count} updated (Total from Markdown: {len(qualities)}).")

def generate_weapons_xml(weapons, output_path):
    try:
        tree = ET.parse(output_path)
        root = tree.getroot()
        weapons_node = root.find("weapons")
        if weapons_node is None:
            weapons_node = ET.SubElement(root, "weapons")
    except FileNotFoundError:
        root = ET.Element("chummer")
        weapons_node = ET.SubElement(root, "weapons")

    existing_weapons = {w.find("name").text: w for w in weapons_node.findall("weapon") if w.find("name") is not None}

    added_count = 0
    updated_count = 0

    for w in weapons:
        name = w['name']
        if name in existing_weapons:
            w_node = existing_weapons[name]
            for field in ['accuracy', 'damage', 'ap', 'mode', 'rc', 'ammo', 'avail', 'cost']:
                md_key = 'acc' if field == 'accuracy' else 'dv' if field == 'damage' else field
                node = w_node.find(field)
                if node is not None:
                    node.text = str(w[md_key])
                else:
                    ET.SubElement(w_node, field).text = str(w[md_key])
            updated_count += 1
        else:
            w_node = ET.SubElement(weapons_node, "weapon")
            hash_id = hashlib.md5(name.encode('utf-8')).hexdigest()
            ET.SubElement(w_node, "id").text = f"CUSTOM_WEAP_{hash_id}"
            ET.SubElement(w_node, "name").text = name
            ET.SubElement(w_node, "accuracy").text = str(w['acc'])
            ET.SubElement(w_node, "damage").text = str(w['dv'])
            ET.SubElement(w_node, "ap").text = str(w['ap'])
            ET.SubElement(w_node, "mode").text = str(w['mode'])
            ET.SubElement(w_node, "rc").text = str(w['rc'])
            ET.SubElement(w_node, "ammo").text = str(w['ammo'])
            ET.SubElement(w_node, "avail").text = str(w['avail'])
            ET.SubElement(w_node, "cost").text = str(w['cost'])
            added_count += 1

    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    # Clean up extra newlines generated by minidom
    xmlstr = '\n'.join([line for line in xmlstr.split('\n') if line.strip()])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xmlstr)
    print(f"Updated {output_path}: {added_count} added, {updated_count} updated (Total from Markdown: {len(weapons)}).")

def main():
    parser = argparse.ArgumentParser(description="Generate Chummer XML files from Markdown.")
    parser.add_argument("file", nargs="?", default="Fan made Shadowrun 7th Edition rules.md")
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = parse_markdown(text)

    qualities = extract_qualities(tokens)
    generate_qualities_xml(qualities, "chummer_plugin/custom_sr7e_qualities.xml")

    tables = extract_tables(tokens)
    weapons = extract_weapons(tables)
    generate_weapons_xml(weapons, "chummer_plugin/custom_sr7e_weapons.xml")

if __name__ == "__main__":
    main()
