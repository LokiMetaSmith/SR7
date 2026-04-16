import re
from analyze_rules import parse_markdown, extract_tables

# Extract accurate weapon stats from the updated Markdown
md_weapons = {}
with open("Fan made Shadowrun 7th Edition rules.md", "r") as f:
    text = f.read()

tokens = parse_markdown(text)
tables = extract_tables(tokens)

for headers, rows in tables:
    if "ACC" in headers and "DV" in headers and "AP" in headers:
        for row in rows:
            name = row[0].replace("**", "").strip()
            if len(row) >= 9:
                acc = row[1].strip()
                dv = row[2].strip()
                ap = row[3].strip()
                mode = row[4].strip()
                rc = row[5].strip()
                range_ = row[6].strip() if len(row) > 6 else ""
                ammo = row[7].strip() if len(row) > 7 else ""
                avail = row[8].strip() if len(row) > 8 else ""
                weight = row[9].strip() if len(row) > 9 else ""

                cost_idx = headers.index("COST") if "COST" in headers else -1
                cost = row[cost_idx].strip() if cost_idx != -1 else ""

                md_weapons[name] = {
                    "ACC": acc,
                    "DV": dv,
                    "AP": ap,
                    "MODE": mode,
                    "RC": rc,
                    "RANGE": range_,
                    "AMMO": ammo,
                    "AVAIL": avail,
                    "WEIGHT": weight,
                    "COST": cost,
                }

with open("Fan made Shadowrun 7th Edition rules.tex", "r") as f:
    tex_lines = f.readlines()

new_tex_lines = []
in_longtblr = False

for line in tex_lines:
    if "\\begin{longtblr}" in line:
        in_longtblr = True
    elif "\\end{longtblr}" in line:
        in_longtblr = False

    if in_longtblr and "&" in line and not line.strip().startswith("%"):
        parts = line.split("&")
        if len(parts) >= 6:
            tex_name = parts[0].strip()
            clean_name = re.sub(r"\\textbf{([^}]+)}", r"\1", tex_name)
            clean_name = re.sub(r"\\gameterm{([^}]+)}", r"\1", clean_name)
            clean_name = clean_name.strip()

            if (
                clean_name in md_weapons
                and "ACC" not in parts[1]
                and "DV" not in parts[2]
            ):
                w = md_weapons[clean_name]

                parts[1] = " " + w["ACC"] + " "
                parts[2] = " " + w["DV"] + " "
                parts[3] = " " + w["AP"] + " "
                if len(parts) > 4:
                    parts[4] = " " + w["MODE"] + " "
                if len(parts) > 5:
                    parts[5] = " " + w["RC"] + " "
                if len(parts) > 6 and "RANGE" in w:
                    parts[6] = " " + w["RANGE"] + " "
                if len(parts) > 7 and "AMMO" in w:
                    parts[7] = " " + w["AMMO"] + " "
                if len(parts) > 8 and "AVAIL" in w:
                    parts[8] = " " + w["AVAIL"] + " "
                if len(parts) > 9 and "WEIGHT" in w:
                    parts[9] = " " + w["WEIGHT"] + " "

                if len(parts) >= 11 and w["COST"]:
                    end_part = parts[-1]
                    cost_str = w["COST"]
                    if (
                        cost_str
                        and not cost_str.endswith("¥")
                        and cost_str != "–"
                        and cost_str != "TBD"
                    ):
                        cost_str += "\\textyen "
                    elif cost_str.endswith("¥"):
                        cost_str = cost_str[:-1] + "\\textyen "

                    if "\\\\" in end_part:
                        parts[-1] = (
                            " " + cost_str + "\\\\" + end_part.split("\\\\", 1)[1]
                        )
                    else:
                        parts[-1] = " " + cost_str + " "

                line = "&".join(parts)

    new_tex_lines.append(line)

with open("Fan made Shadowrun 7th Edition rules.tex", "w") as f:
    f.writelines(new_tex_lines)
