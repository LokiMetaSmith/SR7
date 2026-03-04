import re

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
    tables = re.findall(r"\*\*([^*]+?)\*\*\s*(?:\t|\s+)\*\*ACC\s+DV\s+AP\s+MODE\s+RC\s+RANGE\s+AMMO\s+AVAIL\s+WEIGHT\s+COST\*\*(.*?)(?=\n\n|\Z)", text, re.DOTALL)

    if not tables:
        print("No weapon tables found matching the exact header.")

    for category, content in tables:
        lines = content.strip().split('\n')
        weapons = []
        for line in lines:
            parts = [p.strip() for p in line.split('\t') if p.strip()]
            if len(parts) >= 10:
                name = parts[0]
                acc = parts[1]
                dv = parts[2]
                ap = parts[3]
                mode = parts[4]
                rc = parts[5]
                range_ = parts[6]
                ammo = parts[7]
                avail = parts[8]
                weight = parts[9]
                cost = parts[10] if len(parts) > 10 else "?"
                weapons.append((name, dv, ap, cost))

        print(f"\n{category.strip()}: {len(weapons)} weapons")
        if weapons:
            # Try to calculate average DV
            dvs = []
            for w in weapons:
                try:
                    # extract number from e.g. "9P(f)" or "4S(e)"
                    dv_num = int(re.search(r'\d+', w[1]).group())
                    dvs.append(dv_num)
                except:
                    pass

            if dvs:
                avg_dv = sum(dvs) / len(dvs)
                print(f"  Avg Damage Value: {avg_dv:.2f}")

with open("rules.md", "r") as f:
    text = f.read()

analyze_qualities(text)
analyze_weapons(text)
