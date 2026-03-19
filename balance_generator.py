import argparse
import re
from markdown_it import MarkdownIt

def parse_int_or_float(val_str):
    try:
        val_str = val_str.replace('¥', '').replace(',', '').strip()
        if '(' in val_str:
            val_str = val_str.split('(')[0].strip()
        if '/' in val_str:
            val_str = val_str.split('/')[0].strip()
        return float(val_str)
    except:
        return 0.0

def get_tables_with_positions(text):
    md = MarkdownIt("commonmark").enable("table")
    tokens = md.parse(text)

    tables = []
    in_table = False
    headers = []
    current_table_rows = []
    current_row = []
    start_line = None

    for token in tokens:
        if token.type == "table_open":
            in_table = True
            current_table_rows = []
            headers = []
            if token.map:
                start_line = token.map[0]
                end_line = token.map[1]
        elif token.type == "table_close":
            in_table = False
            tables.append({
                "start": start_line,
                "end": end_line,
                "headers": headers,
                "rows": current_table_rows
            })
        elif in_table and token.type == "tr_open":
            current_row = []
        elif in_table and token.type == "inline":
            current_row.append(token.content)
        elif in_table and token.type == "tr_close":
            if not headers:
                headers = [h.replace("**", "").strip() for h in current_row]
            else:
                current_table_rows.append(current_row)

    return tables

# --- Balancing Constants (referencing rules.md) ---
METATYPE_BASE_STATS = 56
METATYPE_KARMA_PER_POINT = 15
TRAIT_COST_THERMO = 10
TRAIT_COST_LOW_LIGHT = 5
TRAIT_COST_BUILT_TOUGH = 10
TRAIT_COST_REACH = 5
TRAIT_COST_ALLERGY = -15

WEAPON_BASE_COST = 100
WEAPON_DV_MULTIPLIER = 2
WEAPON_AP_COST = 50
WEAPON_MODE_FA = 500
WEAPON_MODE_BF = 200
WEAPON_MODE_SA = 50
WEAPON_RC_COST = 100
WEAPON_AMMO_COST = 5
WEAPON_MULT_PISTOL = 0.8
WEAPON_MULT_HEAVY = 1.5
# ------------------------------------------------

def balance_metatypes(text):
    print("Balancing Metatypes...")
    tables = get_tables_with_positions(text)
    lines = text.split("\n")

    for t in tables:
        if "Race" in t["headers"] and "BOD" in t["headers"] and "Karma Cost" in t["headers"]:
            start_line = t["start"]
            end_line = t["end"]

            new_table_lines = []

            for i in range(start_line, end_line):
                line = lines[i]
                if '---' in line or 'Race |' in line:
                    new_table_lines.append(line)
                    continue

                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 10:
                    name = parts[0].replace('**', '').strip()
                    if 'Human' == name:
                        new_table_lines.append(line)
                        continue

                    stats = []
                    for j in range(1, 10):
                        try:
                            stat_max = int(parts[j].split('/')[1].strip())
                            stats.append(stat_max)
                        except:
                            stats.append(6)

                    traits_col = parts[11] if len(parts) > 11 else ""

                    total_max = sum(stats)
                    diff = total_max - METATYPE_BASE_STATS
                    calculated_cost = max(0, diff * METATYPE_KARMA_PER_POINT)

                    if 'Thermographic Vision' in traits_col: calculated_cost += TRAIT_COST_THERMO
                    if 'Low-Light Vision' in traits_col: calculated_cost += TRAIT_COST_LOW_LIGHT
                    if 'Built Tough' in traits_col:
                        bt_match = re.search(r'Built Tough \((\d+)\)', traits_col)
                        if bt_match:
                            calculated_cost += TRAIT_COST_BUILT_TOUGH * int(bt_match.group(1))
                    if 'Reach (+1)' in traits_col: calculated_cost += TRAIT_COST_REACH
                    if 'Reach (+2)' in traits_col: calculated_cost += TRAIT_COST_REACH * 2
                    if 'Reach (+3)' in traits_col: calculated_cost += TRAIT_COST_REACH * 3
                    if 'Allergy' in traits_col: calculated_cost += TRAIT_COST_ALLERGY

                    calculated_cost = round(calculated_cost / 5) * 5
                    parts[10] = str(calculated_cost)
                    new_line = "| " + " | ".join(parts) + " |"
                    new_table_lines.append(new_line)
                else:
                    new_table_lines.append(line)

            lines[start_line:end_line] = new_table_lines
            return "\n".join(lines)

    print("Metatype table not found!")
    return text

def balance_weapons(text):
    print("Balancing Weapons...")
    tables = get_tables_with_positions(text)
    lines = text.split("\n")

    offset = 0
    # Process from bottom to top so offsets don't invalidate line numbers
    for t in reversed(tables):
        if "ACC" in t["headers"] and "DV" in t["headers"] and "COST" in t["headers"]:
            start_line = t["start"]
            end_line = t["end"]

            # Find the category by looking up a few lines for a heading/strong text
            category = ""
            for i in range(start_line - 1, max(-1, start_line - 5), -1):
                if lines[i].startswith("**"):
                    category = lines[i].replace("**", "").strip()
                    break

            new_table_lines = []

            for i in range(start_line, end_line):
                line = lines[i]
                if not line.strip() or '|' not in line:
                    new_table_lines.append(line)
                    continue

                if '---' in line:
                    new_table_lines.append(line)
                    continue

                col_parts = [p.strip() for p in line.split('|')][1:-1]

                if len(col_parts) >= 9:
                    dv_str = col_parts[2]
                    ap_str = col_parts[3]
                    mode_str = col_parts[4]
                    rc_str = col_parts[5]
                    ammo_str = col_parts[7]

                    dv_match = re.search(r'(\d+)', dv_str)
                    dv = int(dv_match.group(1)) if dv_match else 0

                    ap_match = re.search(r'(-?\d+)', ap_str)
                    ap = int(ap_match.group(1)) if ap_match else 0

                    ammo_match = re.search(r'(\d+)', ammo_str)
                    ammo = int(ammo_match.group(1)) if ammo_match else 0

                    calculated_cost = WEAPON_BASE_COST
                    calculated_cost += (dv ** 2) * WEAPON_DV_MULTIPLIER
                    if ap < 0:
                        calculated_cost += abs(ap) * WEAPON_AP_COST

                    if 'FA' in mode_str:
                        calculated_cost += WEAPON_MODE_FA
                    elif 'BF' in mode_str:
                        calculated_cost += WEAPON_MODE_BF
                    elif 'SA' in mode_str:
                        calculated_cost += WEAPON_MODE_SA

                    rc_match = re.search(r'(\d+)', rc_str)
                    rc = int(rc_match.group(1)) if rc_match else 0
                    calculated_cost += rc * WEAPON_RC_COST

                    calculated_cost += ammo * WEAPON_AMMO_COST

                    if 'Pistol' in category or 'Hold-Out' in category:
                        calculated_cost *= WEAPON_MULT_PISTOL
                    elif 'Sniper' in category or 'Cannon' in category or 'Machine Gun' in category:
                        calculated_cost *= WEAPON_MULT_HEAVY

                    if calculated_cost > 10000:
                        calculated_cost = round(calculated_cost / 1000) * 1000
                    elif calculated_cost > 1000:
                        calculated_cost = round(calculated_cost / 100) * 100
                    elif calculated_cost > 100:
                        calculated_cost = round(calculated_cost / 50) * 50
                    else:
                        calculated_cost = round(calculated_cost / 10) * 10

                    if len(col_parts) > 0:
                        original_cost_str = col_parts[-1]
                        new_cost_str = f"{int(calculated_cost)}¥" if '¥' in original_cost_str or original_cost_str.isdigit() else str(int(calculated_cost))
                        if original_cost_str != '-' and original_cost_str != '':
                            col_parts[-1] = new_cost_str

                    new_line = "| " + " | ".join(col_parts) + " |"
                    new_table_lines.append(new_line)
                else:
                    new_table_lines.append(line)

            lines[start_line:end_line] = new_table_lines

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Balance Metatypes and Weapons in Shadowrun 7E Homebrew rules markdown.")
    parser.add_argument(
        "file",
        nargs="?",
        default="Fan made Shadowrun 7th Edition rules.md",
        help="Path to the markdown file to balance (default: 'Fan made Shadowrun 7th Edition rules.md')"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path to save the balanced markdown file. If not provided, overwrites the input file."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the balancing operations without saving changes to any file."
    )
    args = parser.parse_args()

    input_filepath = args.file
    output_filepath = args.output if args.output else input_filepath

    try:
        with open(input_filepath, 'r') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_filepath}' not found.")
        return
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return

    print("Starting balancing...")
    text = balance_metatypes(text)
    text = balance_weapons(text)

    if args.dry_run:
        print("Dry run complete. No files were modified.")
        return

    try:
        with open(output_filepath, 'w') as f:
            f.write(text)
        print(f"Balancing complete! The markdown file '{output_filepath}' has been updated.")
    except Exception as e:
        print(f"Error writing to file '{output_filepath}': {e}")

if __name__ == "__main__":
    main()
