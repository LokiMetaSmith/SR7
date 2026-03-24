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
    tables = []
    in_table = False
    headers = []
    current_table_rows = []
    current_row = []

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
        elif in_table and token.type == "inline":
            current_row.append(token.content)
        elif in_table and token.type == "tr_close":
            if not headers:
                headers = [h.replace("**", "").strip() for h in current_row]
            else:
                current_table_rows.append(current_row)
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
