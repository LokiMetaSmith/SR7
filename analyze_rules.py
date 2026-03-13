import argparse
import re
import statistics

def analyze_qualities(text):
    print("=== Qualities Analysis ===")

    qualities = []
    for line in text.split("\n"):
        line = line.strip()

        m = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Karma\s*\((.+?)\)", line)
        if m:
            name, cost, tags = m.groups()
            qualities.append((name, cost, tags))
            continue

        m2 = re.match(r"^\*\*(.+?)\*\*\s*\\\-\s*(.+?)\s*Quality\)", line)
        if m2:
             qualities.append((m2.group(1), "?", m2.group(2)))

    print(f"Total Qualities Found: {len(qualities)}")

    # Categorize by tags
    tags_count = {}
    for q in qualities:
        tags = [t.strip() for t in q[2].split(",")]
        for tag in tags:
            tag = tag.replace(" Quality", "")
            tags_count[tag] = tags_count.get(tag, 0) + 1

    print("\nQualities by Type:")
    for tag, count in sorted(tags_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tag}: {count}")

def analyze_weapons(text):
    print("\n=== Weapons Analysis ===")

    # Tables start with something like "**Hold-Outs**		**ACC    	DV        	AP    	MODE    RC	RANGE    AMMO    AVAIL    WEIGHT	COST**"
    tables = re.findall(r"\*\*([^*]+?)\*\*\s*(?:\t|\s+)\*\*(.*?COST)\*\*(.*?)(?=\n\n|\Z)", text, re.DOTALL)

    if not tables:
        print("No weapon tables found matching the exact header.")

    for category, header, content in tables:
        lines = content.strip().split('\n')
        weapons = []
        for line in lines:
            parts = [p.strip() for p in line.split('\t') if p.strip()]
            if len(parts) >= 3:
                name = parts[0]

                # Find cost
                cost = "?"
                for p in reversed(parts):
                    if '¥' in p or p.isdigit() or p.replace(',', '').isdigit():
                        cost = p
                        break

                # Find DV
                dv = "?"
                for p in parts[1:]:
                    if re.match(r'^\d+[PS](?:\(.*?\))?$', p) or re.match(r'^\d+$', p) and int(p) > 0:
                        dv = p
                        break
                if dv == "?" and len(parts) >= 3:
                    # Fallback to a common column if missing P/S indicator
                    dv = parts[1] if 'DV' in header and header.index('DV') < header.index('AP') else parts[2]

                weapons.append((name, dv, cost))

        print(f"\n{category.strip()}: {len(weapons)} weapons")
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

def analyze_metatypes(text):
    print("\n=== Metatype Analysis ===")

    # Simple regex to extract metatype names and karma costs from the table
    # Format: **Human**		1 / 6	1 / 6	1 / 6	1 / 6	1 / 6	1 / 6	1 / 6	1 / 6	2 / 7	0

    metatypes = []
    lines = text.split("\n")
    in_table = False
    for line in lines:
        if "**Race:" in line:
            in_table = True
            continue
        if in_table and line.strip() == "":
            in_table = False
            continue

        if in_table and line.startswith("**") and not "Race:" in line:
            parts = line.split("\t")
            if len(parts) >= 10:
                name = parts[0].replace("**", "").strip()
                cost = parts[-1].strip()
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

    analyze_qualities(text)
    analyze_weapons(text)
    analyze_metatypes(text)

if __name__ == "__main__":
    main()
