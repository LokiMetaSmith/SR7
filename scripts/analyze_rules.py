import argparse
import re
import statistics
from markdown_it import MarkdownIt

def parse_markdown(text):
    md = MarkdownIt("commonmark").enable("table")
    return md.parse(text)

def analyze_qualities(tokens):
    print("=== Qualities Analysis ===")

    qualities = []

    for token in tokens:
        if token.type == "inline":
            m = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Karma\s*\((.+?)\)", token.content)
            if m:
                name, cost, tags = m.groups()
                qualities.append((name, cost, tags))
                continue

            m2 = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Karma\s*(?:\\|\Z|\n|$)", token.content)
            if m2:
                name, cost = m2.groups()
                qualities.append((name, cost, "?"))
                continue

            m3 = re.match(r"^\*\*(.+?)\*\*\s*-\s*(.+?)\s*Karma\s*\((.+?)\)", token.content)
            if m3:
                name, cost, tags = m3.groups()
                qualities.append((name, cost, tags))
                continue

            m4 = re.match(r"^\*\*(.+?)\*\*\s*-\s*(.+?)\s*Karma\s*(?:\\|\Z|\n|$)", token.content)
            if m4:
                name, cost = m4.groups()
                qualities.append((name, cost, "?"))
                continue

            m5 = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Quality\)", token.content)
            if m5:
                qualities.append((m5.group(1), "?", m5.group(2)))
                continue

    print(f"Total Qualities Found: {len(qualities)}")

    # Categorize by tags
    tags_count = {}
    for q in qualities:
        if q[2] == "?":
            continue
        tags = [t.strip() for t in q[2].split(",")]
        for tag in tags:
            tag = tag.replace(" Quality", "")
            tags_count[tag] = tags_count.get(tag, 0) + 1

    print("\nQualities by Type:")
    for tag, count in sorted(tags_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tag}: {count}")

def extract_tables(tokens):
    print("\n=== Extracting Tables ===")
    tables = []
    in_table = False
    in_thead = False
    in_tbody = False
    in_tr = False
    in_th = False
    in_td = False

    current_headers = []
    current_rows = []
    current_row = []
    current_cell = ""

    for token in tokens:
        if token.type == "table_open":
            in_table = True
            current_headers = []
            current_rows = []
        elif token.type == "thead_open":
            in_thead = True
        elif token.type == "tbody_open":
            in_tbody = True
        elif token.type == "tr_open":
            in_tr = True
            current_row = []
        elif token.type == "th_open":
            in_th = True
            current_cell = ""
        elif token.type == "td_open":
            in_td = True
            current_cell = ""
        elif token.type == "inline" and (in_th or in_td):
            current_cell += token.content
        elif token.type == "th_close":
            in_th = False
            current_headers.append(current_cell.strip())
        elif token.type == "td_close":
            in_td = False
            current_row.append(current_cell.strip())
        elif token.type == "tr_close":
            in_tr = False
            if in_tbody and current_row:
                current_rows.append(current_row)
        elif token.type == "table_close":
            in_table = False

            # Enforce Master Templates
            # Weapons Table
            if "Weapon Name" in current_headers or "DV" in current_headers:
                expected_weapons_headers = ["Weapon Name", "ACC", "DV", "AP", "MODE", "RC", "AMMO", "AVAIL", "COST"]
                if current_headers != expected_weapons_headers:
                    print(f"WARNING: Weapon table headers do not match Master Template!")
                    print(f"Expected: {expected_weapons_headers}")
                    print(f"Got:      {current_headers}")
            # Augmentations Table
            elif "Augmentation" in current_headers:
                expected_aug_headers = ["Augmentation", "Type", "Essence", "Cost (¥)", "Effect"]
                if current_headers != expected_aug_headers:
                    print(f"WARNING: Augmentations table headers do not match Master Template!")
            # Armor Table
            elif "Item" in current_headers and "Rating / Stats" in current_headers:
                expected_armor_headers = ["Item", "Type", "Rating / Stats", "Capacity", "Cost (¥)", "Description"]
                if current_headers != expected_armor_headers:
                    print(f"WARNING: Armor table headers do not match Master Template!")

            if current_headers and current_rows:
                tables.append((current_headers, current_rows))

    print(f"Extracted {len(tables)} tables.")
    return tables


def analyze_weapons(tables):
    print("\n=== Weapons Analysis ===")

    found_weapons = False

    for headers, rows in tables:
        if "ACC" in headers and "DV" in headers and "AP" in headers:
            found_weapons = True
            weapons = []

            # Find indices
            acc_idx = headers.index("ACC") if "ACC" in headers else -1
            dv_idx = headers.index("DV") if "DV" in headers else -1
            ap_idx = headers.index("AP") if "AP" in headers else -1
            cost_idx = headers.index("COST") if "COST" in headers else -1

            if dv_idx == -1 or cost_idx == -1:
                continue

            for row in rows:
                if len(row) > max(dv_idx, cost_idx):
                    name = row[0].replace("**", "").strip()
                    dv = row[dv_idx].strip()
                    cost = row[cost_idx].strip()
                    if dv and cost and dv != "–" and cost != "–":
                        weapons.append((name, dv, cost))

            print(f"\nWeapons table ({len(weapons)} weapons)")
            if weapons:
                # Try to calculate average DV and identify outliers based on DV/Cost
                dvs = []
                ratios = []
                valid_weapons = []

                for w in weapons:
                    try:
                        # extract number from e.g. "9P(f)" or "4S(e)"
                        m_dv = re.search(r'\d+', w[1])
                        if not m_dv:
                            continue
                        dv_num = int(m_dv.group())
                        dvs.append(dv_num)

                        cost_str = w[2].replace('¥', '').replace(',', '')
                        if cost_str.isdigit():
                            cost_num = int(cost_str)
                            if cost_num > 0:
                                ratio = dv_num / cost_num
                                ratios.append(ratio)
                                valid_weapons.append((w[0], dv_num, cost_num, ratio))
                    except:
                        pass

                if dvs:
                    avg_dv = sum(dvs) / len(dvs)
                    print(f"  Avg Damage Value: {avg_dv:.2f}")

                if len(ratios) >= 2:
                    mean_ratio = statistics.mean(ratios)
                    stdev_ratio = statistics.stdev(ratios)

                    outliers = []
                    for vw in valid_weapons:
                        name, dv, cost, ratio = vw
                        if abs(ratio - mean_ratio) > 2 * stdev_ratio:
                            outliers.append(vw)

                    if outliers:
                        print(f"  Outliers detected (>2 StdDev from Mean DV/Cost {mean_ratio:.5f}):")
                        for vw in outliers:
                            print(f"    - {vw[0]}: DV={vw[1]}, Cost={vw[2]}¥ (Ratio: {vw[3]:.5f})")
                    else:
                        print(f"  No outliers detected (Mean DV/Cost {mean_ratio:.5f})")

    if not found_weapons:
        print("No weapon tables found matching the exact header.")

def analyze_metatypes(tables):
    print("\n=== Metatype Analysis ===")

    metatypes = []

    for headers, rows in tables:
        if "Race" in headers and "BOD" in headers and "Karma Cost" in headers:
            cost_idx = headers.index("Karma Cost")
            for row in rows:
                if len(row) > cost_idx:
                    name = row[0].replace("**", "").strip()
                    cost = row[cost_idx].strip()
                    metatypes.append((name, cost))

    for m in metatypes:
        print(f"  {m[0]}: {m[1]} Karma")

def main():
    parser = argparse.ArgumentParser(description="Analyze Shadowrun 7E Homebrew rules markdown.")
    parser.add_argument(
        "file",
        nargs="?",
        default="Fan made Shadowrun 7th Edition rules.md",
        help="Path to the markdown file to analyze (default: 'Fan made Shadowrun 7th Edition rules.md')"
    )
    args = parser.parse_args()

    try:
        with open(args.file, "r") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
        return
    except Exception as e:
        print(f"Error reading file '{args.file}': {e}")
        return

    tokens = parse_markdown(text)
    tables = extract_tables(tokens)

    analyze_qualities(tokens)
    analyze_weapons(tables)
    analyze_metatypes(tables)

if __name__ == "__main__":
    main()
