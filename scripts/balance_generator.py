import argparse
import re
from markdown_it import MarkdownIt


def parse_int_or_float(val_str):
    try:
        val_str = val_str.replace("¥", "").replace(",", "").strip()
        if "(" in val_str:
            val_str = val_str.split("(")[0].strip()
        if "/" in val_str:
            val_str = val_str.split("/")[0].strip()
        return float(val_str)
    except Exception:
        return 0.0


def get_tables_with_positions(text):
    md = MarkdownIt("commonmark").enable("table")
    tokens = md.parse(text)

    tables = []
    in_table = False
    in_th_td = False
    headers = []
    current_table_rows = []
    current_row = []
    cell_content = []
    start_line = None
    end_line = None

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
            tables.append(
                {
                    "start": start_line,
                    "end": end_line,
                    "headers": headers,
                    "rows": current_table_rows,
                }
            )
        elif in_table and token.type == "tr_open":
            current_row = []
        elif in_table and token.type in ["th_open", "td_open"]:
            in_th_td = True
            cell_content = []
        elif in_table and in_th_td and token.type == "inline":
            cell_content.append(token.content)
        elif in_table and token.type in ["th_close", "td_close"]:
            in_th_td = False
            current_row.append("".join(cell_content))
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

AUGMENTATION_BASE_COST = 500
AUGMENTATION_ESSENCE_PENALTY = 10000
AUGMENTATION_MULT_CYBER = 1.0
AUGMENTATION_MULT_BIO = 1.5
AUGMENTATION_MULT_NANO = 2.0

ARMOR_BASE_COST = 100
ARMOR_RATING_MULTIPLIER = 5
ARMOR_CAPACITY_COST = 20

DEVICE_BASE_COST = 100
DEVICE_RTG_MULTIPLIER = 50
DEVICE_ATTR_COST = 200
DEVICE_MULT_COMM = 1.0
DEVICE_MULT_DECK = 5.0
DEVICE_MULT_RIG = 3.0
# ------------------------------------------------


def balance_metatypes(text):
    print("Balancing Metatypes...")
    tables = get_tables_with_positions(text)
    lines = text.split("\n")

    for t in tables:
        if (
            "Race" in t["headers"]
            and "BOD" in t["headers"]
            and "Karma Cost" in t["headers"]
        ):
            start_line = t["start"]
            end_line = t["end"]

            new_table_lines = []

            # Reconstruct the header and separator
            new_table_lines.append("| " + " | ".join(t["headers"]) + " |")
            new_table_lines.append("|" + "|".join([" :--- " for _ in t["headers"]]) + "|")

            for row in t["rows"]:
                if len(row) >= 10:
                    name = row[0].replace("**", "").strip()
                    if "Human" == name:
                        new_table_lines.append("| " + " | ".join(row) + " |")
                        continue

                    stats = []
                    for j in range(1, 10):
                        try:
                            stat_max = int(row[j].split("/")[1].strip())
                            stats.append(stat_max)
                        except Exception:
                            stats.append(6)

                    traits_col = row[11] if len(row) > 11 else ""

                    total_max = sum(stats)
                    diff = total_max - METATYPE_BASE_STATS
                    calculated_cost = max(0, diff * METATYPE_KARMA_PER_POINT)

                    if "Thermographic Vision" in traits_col:
                        calculated_cost += TRAIT_COST_THERMO
                    if "Low-Light Vision" in traits_col:
                        calculated_cost += TRAIT_COST_LOW_LIGHT
                    if "Built Tough" in traits_col:
                        bt_match = re.search(r"Built Tough \((\d+)\)", traits_col)
                        if bt_match:
                            calculated_cost += TRAIT_COST_BUILT_TOUGH * int(
                                bt_match.group(1)
                            )
                    if "Reach (+1)" in traits_col:
                        calculated_cost += TRAIT_COST_REACH
                    if "Reach (+2)" in traits_col:
                        calculated_cost += TRAIT_COST_REACH * 2
                    if "Reach (+3)" in traits_col:
                        calculated_cost += TRAIT_COST_REACH * 3
                    if "Allergy" in traits_col:
                        calculated_cost += TRAIT_COST_ALLERGY

                    calculated_cost = round(calculated_cost / 5) * 5

                    # Update cost column
                    cost_idx = t["headers"].index("Karma Cost")
                    row[cost_idx] = str(calculated_cost)

                    new_table_lines.append("| " + " | ".join(row) + " |")
                else:
                    new_table_lines.append("| " + " | ".join(row) + " |")

            lines[start_line:end_line] = new_table_lines
            return "\n".join(lines)

    print("Metatype table not found!")
    return text


def balance_weapons(text):
    print("Balancing Weapons...")
    tables = get_tables_with_positions(text)
    lines = text.split("\n")

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
            new_table_lines.append("| " + " | ".join(t["headers"]) + " |")
            new_table_lines.append("|" + "|".join([" :--- " for _ in t["headers"]]) + "|")

            for row in t["rows"]:
                if len(row) >= 9:
                    dv_str = row[t["headers"].index("DV")] if "DV" in t["headers"] else ""
                    ap_str = row[t["headers"].index("AP")] if "AP" in t["headers"] else ""
                    mode_str = row[t["headers"].index("MODE")] if "MODE" in t["headers"] else ""
                    rc_str = row[t["headers"].index("RC")] if "RC" in t["headers"] else ""
                    ammo_str = row[t["headers"].index("AMMO")] if "AMMO" in t["headers"] else ""

                    dv_match = re.search(r"(\d+)", dv_str)
                    dv = int(dv_match.group(1)) if dv_match else 0

                    ap_match = re.search(r"(-?\d+)", ap_str)
                    ap = int(ap_match.group(1)) if ap_match else 0

                    ammo_match = re.search(r"(\d+)", ammo_str)
                    ammo = int(ammo_match.group(1)) if ammo_match else 0

                    calculated_cost = WEAPON_BASE_COST
                    calculated_cost += (dv**2) * WEAPON_DV_MULTIPLIER
                    if ap < 0:
                        calculated_cost += abs(ap) * WEAPON_AP_COST

                    if "FA" in mode_str:
                        calculated_cost += WEAPON_MODE_FA
                    elif "BF" in mode_str:
                        calculated_cost += WEAPON_MODE_BF
                    elif "SA" in mode_str:
                        calculated_cost += WEAPON_MODE_SA

                    rc_match = re.search(r"(\d+)", rc_str)
                    rc = int(rc_match.group(1)) if rc_match else 0
                    calculated_cost += rc * WEAPON_RC_COST

                    calculated_cost += ammo * WEAPON_AMMO_COST

                    if "Pistol" in category or "Hold-Out" in category:
                        calculated_cost *= WEAPON_MULT_PISTOL
                    elif (
                        "Sniper" in category
                        or "Cannon" in category
                        or "Machine Gun" in category
                    ):
                        calculated_cost *= WEAPON_MULT_HEAVY

                    if calculated_cost > 10000:
                        calculated_cost = round(calculated_cost / 1000) * 1000
                    elif calculated_cost > 1000:
                        calculated_cost = round(calculated_cost / 100) * 100
                    elif calculated_cost > 100:
                        calculated_cost = round(calculated_cost / 50) * 50
                    else:
                        calculated_cost = round(calculated_cost / 10) * 10

                    if "COST" in t["headers"]:
                        cost_idx = t["headers"].index("COST")
                        original_cost_str = row[cost_idx]
                        new_cost_str = (
                            f"{int(calculated_cost)}¥"
                            if "¥" in original_cost_str or original_cost_str.isdigit()
                            else str(int(calculated_cost))
                        )
                        if original_cost_str != "-" and original_cost_str != "":
                            row[cost_idx] = new_cost_str

                    new_table_lines.append("| " + " | ".join(row) + " |")
                else:
                    new_table_lines.append("| " + " | ".join(row) + " |")

            lines[start_line:end_line] = new_table_lines

    return "\n".join(lines)


def balance_augmentations(text):
    print("Balancing Augmentations...")
    tables = get_tables_with_positions(text)
    lines = text.split("\n")

    for t in reversed(tables):
        if "Augmentation" in t["headers"] and "Type" in t["headers"] and "Cost (¥)" in t["headers"]:
            start_line = t["start"]
            end_line = t["end"]

            new_table_lines = []
            new_table_lines.append("| " + " | ".join(t["headers"]) + " |")
            new_table_lines.append("|" + "|".join([" :--- " for _ in t["headers"]]) + "|")

            for row in t["rows"]:
                if len(row) >= 4:
                    aug_type = row[t["headers"].index("Type")] if "Type" in t["headers"] else ""
                    essence_str = row[t["headers"].index("Essence")] if "Essence" in t["headers"] else ""

                    essence = parse_int_or_float(essence_str)

                    calculated_cost = AUGMENTATION_BASE_COST

                    rating_match = re.search(r"Rtg\s*(\d+)", row[t["headers"].index("Augmentation")])
                    rating = int(rating_match.group(1)) if rating_match else 1

                    if "Wired Reflexes" in row[t["headers"].index("Augmentation")]:
                        if "I" in row[t["headers"].index("Augmentation")]: rating = 1
                        if "II" in row[t["headers"].index("Augmentation")]: rating = 2
                        if "III" in row[t["headers"].index("Augmentation")]: rating = 3

                    if "Synaptic Booster" in row[t["headers"].index("Augmentation")]:
                        if "I" in row[t["headers"].index("Augmentation")]: rating = 1
                        if "II" in row[t["headers"].index("Augmentation")]: rating = 2
                        if "III" in row[t["headers"].index("Augmentation")]: rating = 3

                    calculated_cost = AUGMENTATION_BASE_COST
                    calculated_cost += (rating ** 2) * 5000

                    essence_penalty = max(0, essence) * AUGMENTATION_ESSENCE_PENALTY
                    calculated_cost += essence_penalty

                    if "Bio" in aug_type:
                        calculated_cost *= AUGMENTATION_MULT_BIO
                    elif "Nano" in aug_type or "Genetic" in aug_type:
                        calculated_cost *= AUGMENTATION_MULT_NANO
                    else:
                        calculated_cost *= AUGMENTATION_MULT_CYBER

                    calculated_cost = round(calculated_cost / 500) * 500

                    if "Cost (¥)" in t["headers"]:
                        cost_idx = t["headers"].index("Cost (¥)")
                        original_cost_str = row[cost_idx]
                        if original_cost_str.strip() != "" and original_cost_str.strip() != "-":
                            if "/" in original_cost_str:
                                new_cost_str = f"{int(calculated_cost):,} / Lvl"
                            else:
                                new_cost_str = f"{int(calculated_cost):,}"
                            row[cost_idx] = new_cost_str

                    new_table_lines.append("| " + " | ".join(row) + " |")
                else:
                    new_table_lines.append("| " + " | ".join(row) + " |")

            lines[start_line:end_line] = new_table_lines

    return "\n".join(lines)


def balance_armor(text):
    print("Balancing Armor...")
    tables = get_tables_with_positions(text)
    lines = text.split("\n")

    for t in reversed(tables):
        if "Item" in t["headers"] and "Rating / Stats" in t["headers"] and "Cost (¥)" in t["headers"] and "Capacity" in t["headers"]:
            start_line = t["start"]
            end_line = t["end"]

            new_table_lines = []
            new_table_lines.append("| " + " | ".join(t["headers"]) + " |")
            new_table_lines.append("|" + "|".join([" :--- " for _ in t["headers"]]) + "|")

            for row in t["rows"]:
                if len(row) >= 5:
                    item_type = row[t["headers"].index("Type")] if "Type" in t["headers"] else ""
                    if "Armor" not in item_type:
                        new_table_lines.append("| " + " | ".join(row) + " |")
                        continue

                    rating_str = row[t["headers"].index("Rating / Stats")] if "Rating / Stats" in t["headers"] else ""
                    capacity_str = row[t["headers"].index("Capacity")] if "Capacity" in t["headers"] else ""

                    rating = parse_int_or_float(rating_str)
                    capacity = parse_int_or_float(capacity_str)

                    calculated_cost = ARMOR_BASE_COST
                    calculated_cost += (rating ** 2) * ARMOR_RATING_MULTIPLIER
                    calculated_cost += capacity * ARMOR_CAPACITY_COST

                    calculated_cost = round(calculated_cost / 50) * 50

                    if "Cost (¥)" in t["headers"]:
                        cost_idx = t["headers"].index("Cost (¥)")
                        original_cost_str = row[cost_idx]
                        if original_cost_str.strip() != "" and original_cost_str.strip() != "-":
                            row[cost_idx] = f"{int(calculated_cost):,}"

                    new_table_lines.append("| " + " | ".join(row) + " |")
                else:
                    new_table_lines.append("| " + " | ".join(row) + " |")

            lines[start_line:end_line] = new_table_lines

    return "\n".join(lines)


def balance_devices(text):
    print("Balancing Devices...")
    tables = get_tables_with_positions(text)
    lines = text.split("\n")

    for t in reversed(tables):
        if "Device Type" in t["headers"] and "Device Rtg" in t["headers"] and "A / S / D / F" in t["headers"] and "Base Cost (¥)" in t["headers"]:
            start_line = t["start"]
            end_line = t["end"]

            new_table_lines = []
            new_table_lines.append("| " + " | ".join(t["headers"]) + " |")
            new_table_lines.append("|" + "|".join([" :--- " for _ in t["headers"]]) + "|")

            for row in t["rows"]:
                if len(row) >= 5:
                    device_type = row[t["headers"].index("Device Type")] if "Device Type" in t["headers"] else ""
                    rtg_str = row[t["headers"].index("Device Rtg")] if "Device Rtg" in t["headers"] else ""
                    attrs_str = row[t["headers"].index("A / S / D / F")] if "A / S / D / F" in t["headers"] else ""

                    rtg = parse_int_or_float(rtg_str)

                    attrs_sum = 0
                    for attr in attrs_str.split("/"):
                        attrs_sum += parse_int_or_float(attr.strip())

                    calculated_cost = DEVICE_BASE_COST
                    calculated_cost += (rtg ** 2) * DEVICE_RTG_MULTIPLIER
                    calculated_cost += attrs_sum * DEVICE_ATTR_COST

                    if "Deck" in device_type:
                        calculated_cost *= DEVICE_MULT_DECK
                    elif "Rigger" in device_type:
                        calculated_cost *= DEVICE_MULT_RIG
                    else:
                        calculated_cost *= DEVICE_MULT_COMM

                    calculated_cost = round(calculated_cost / 100) * 100

                    if "Base Cost (¥)" in t["headers"]:
                        cost_idx = t["headers"].index("Base Cost (¥)")
                        original_cost_str = row[cost_idx]
                        if original_cost_str.strip() != "" and original_cost_str.strip() != "-":
                            row[cost_idx] = f"{int(calculated_cost):,}"

                    new_table_lines.append("| " + " | ".join(row) + " |")
                else:
                    new_table_lines.append("| " + " | ".join(row) + " |")

            lines[start_line:end_line] = new_table_lines

    return "\n".join(lines)


def balance_lifestyles(text):
    # Lifestyles don't have a formula to apply, so we'll just return the text
    # This acts as a hook if we ever want to do something with Lifestyles balancing later
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Balance Metatypes and Weapons in Shadowrun 7E Homebrew rules markdown."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="Fan made Shadowrun 7th Edition rules.md",
        help="Path to the markdown file to balance (default: 'Fan made Shadowrun 7th Edition rules.md')",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path to save the balanced markdown file. If not provided, overwrites the input file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the balancing operations without saving changes to any file.",
    )
    args = parser.parse_args()

    input_filepath = args.file
    output_filepath = args.output if args.output else input_filepath

    try:
        with open(input_filepath, "r") as f:
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
    text = balance_augmentations(text)
    text = balance_armor(text)
    text = balance_devices(text)
    text = balance_lifestyles(text)

    if args.dry_run:
        print("Dry run complete. No files were modified.")
        return

    try:
        with open(output_filepath, "w") as f:
            f.write(text)
        print(
            f"Balancing complete! The markdown file '{output_filepath}' has been updated."
        )
    except Exception as e:
        print(f"Error writing to file '{output_filepath}': {e}")


if __name__ == "__main__":
    main()
