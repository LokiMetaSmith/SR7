import re

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

def balance_metatypes(text):
    print("Balancing Metatypes...")
    # Finding the metatype table
    table_regex = re.compile(r"(\| Race \| BOD \| AGI \| REA \| STR \| WIL \| LOG \| INT \| CHA \| EDG \| Karma Cost \| Traits \|.*?\n(?:\|---|.*?)+\n(?:\|.*?\|\n)+)", re.DOTALL)
    match = table_regex.search(text)

    if not match:
        print("Metatype table not found!")
        return text

    table_text = match.group(1)
    new_table_lines = []

    for line in table_text.strip().split('\n'):
        if '---' in line or 'Race |' in line:
            new_table_lines.append(line)
            continue

        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 10:
            name = parts[0].replace('**', '').strip()
            # If it's human, skip balancing and keep at 0
            if 'Human' == name:
                new_table_lines.append(line)
                continue

            # Stats are in format: min / max
            stats = []
            for i in range(1, 10): # BOD to EDG
                try:
                    stat_max = int(parts[i].split('/')[1].strip())
                    stats.append(stat_max)
                except:
                    stats.append(6) # Fallback max

            # Human maxes are all 6, except CHA 7, EDG 7
            # Base human total max = 6+6+6+6+6+6+6+7+7 = 56
            # Total stats for human max:
            # BOD(6) AGI(6) REA(6) STR(6) WIL(6) LOG(6) INT(6) CHA(7) EDG(7)
            # Actually let's just do a direct calculation: sum of maxes.
            # Every point above human baseline total costs 10 karma
            # Some traits also add karma cost.

            traits_col = parts[11] if len(parts) > 11 else ""
            traits = [t.strip() for t in traits_col.split(',')]

            # Simple heuristic
            # Calculate total max attributes difference from 56
            total_max = sum(stats)
            diff = total_max - 56

            # Base cost is 15 karma per stat point over baseline
            calculated_cost = max(0, diff * 15)

            # Traits modifiers
            if 'Thermographic Vision' in traits_col: calculated_cost += 10
            if 'Low-Light Vision' in traits_col: calculated_cost += 5
            if 'Built Tough' in traits_col:
                # Add 10 per level of built tough
                bt_match = re.search(r'Built Tough \((\d+)\)', traits_col)
                if bt_match:
                    calculated_cost += 10 * int(bt_match.group(1))
            if 'Reach (+1)' in traits_col: calculated_cost += 5
            if 'Reach (+2)' in traits_col: calculated_cost += 10
            if 'Reach (+3)' in traits_col: calculated_cost += 15
            if 'Allergy' in traits_col: calculated_cost -= 15

            # Round to nearest 5
            calculated_cost = round(calculated_cost / 5) * 5

            # Replace cost in the line
            # The cost is the 10th column (index 10 in parts)
            parts[10] = str(calculated_cost)
            new_line = "| " + " | ".join(parts) + " |"
            new_table_lines.append(new_line)
        else:
            new_table_lines.append(line)

    return text.replace(table_text, '\n'.join(new_table_lines) + '\n')

def balance_weapons(text):
    print("Balancing Weapons...")
    # Find all tables that have COST
    tables = re.findall(r"(\*\*([^*]+?)\*\*\s*(?:\t|\s+)\*\*(.*?COST)\*\*(.*?))(?=\n\n|\Z)", text, re.DOTALL)

    for full_match, category, header, content in tables:
        new_content_lines = []
        lines = content.strip().split('\n')

        for line in lines:
            if not line.strip() or '|' not in line:
                new_content_lines.append(line)
                continue

            if '---' in line:
                new_content_lines.append(line)
                continue

            parts = [p.strip() for p in line.split('|')]
            # Clean up empty strings from split
            # Actually, standard markdown tables start and end with |
            col_parts = [p.strip() for p in line.split('|')][1:-1]

            if len(col_parts) >= 9:
                # Based on standard format:
                # Name | ACC | DV | AP | MODE | RC | RANGE | AMMO | AVAIL | WEIGHT | COST
                name = col_parts[0]

                # Try to extract stats
                dv_str = col_parts[2]
                ap_str = col_parts[3]
                mode_str = col_parts[4]
                rc_str = col_parts[5]
                ammo_str = col_parts[7]

                # Parse DV
                dv_match = re.search(r'(\d+)', dv_str)
                dv = int(dv_match.group(1)) if dv_match else 0

                # Parse AP
                ap_match = re.search(r'(-?\d+)', ap_str)
                ap = int(ap_match.group(1)) if ap_match else 0

                # Parse Ammo
                ammo_match = re.search(r'(\d+)', ammo_str)
                ammo = int(ammo_match.group(1)) if ammo_match else 0

                # Calculate balanced cost
                # Base cost
                calculated_cost = 100

                # Factor in Damage (Exponential scale for high damage)
                calculated_cost += (dv ** 2) * 2

                # Factor in AP (Negative AP increases cost)
                if ap < 0:
                    calculated_cost += abs(ap) * 50

                # Factor in Firing Mode
                if 'FA' in mode_str:
                    calculated_cost += 500
                elif 'BF' in mode_str:
                    calculated_cost += 200
                elif 'SA' in mode_str:
                    calculated_cost += 50

                # Factor in RC (Recoil Compensation)
                rc_match = re.search(r'(\d+)', rc_str)
                rc = int(rc_match.group(1)) if rc_match else 0
                calculated_cost += rc * 100

                # Factor in Ammo Capacity
                calculated_cost += ammo * 5

                # Adjust for category
                if 'Pistol' in category or 'Hold-Out' in category:
                    calculated_cost *= 0.8
                elif 'Sniper' in category or 'Cannon' in category or 'Machine Gun' in category:
                    calculated_cost *= 1.5

                # Rounding to nice numbers
                if calculated_cost > 10000:
                    calculated_cost = round(calculated_cost / 1000) * 1000
                elif calculated_cost > 1000:
                    calculated_cost = round(calculated_cost / 100) * 100
                elif calculated_cost > 100:
                    calculated_cost = round(calculated_cost / 50) * 50
                else:
                    calculated_cost = round(calculated_cost / 10) * 10

                # Replace the cost
                # We need to find the right index for COST. It's usually the last or second to last.
                # Just replace the last element if it looks like a cost
                cost_idx = -1

                # Ensure the column exists
                if len(col_parts) > cost_idx:
                    # Update the cost string with the new balanced cost
                    original_cost_str = col_parts[-1]
                    # Keep ¥ if it was there
                    new_cost_str = f"{int(calculated_cost)}¥" if '¥' in original_cost_str or original_cost_str.isdigit() else str(int(calculated_cost))

                    if original_cost_str != '-' and original_cost_str != '':
                        col_parts[-1] = new_cost_str

                # Reconstruct line
                new_line = "| " + " | ".join(col_parts) + " |"
                new_content_lines.append(new_line)
            else:
                new_content_lines.append(line)

        # Replace the old content with the new content
        new_content_text = '\n'.join(new_content_lines)
        text = text.replace(content.strip(), new_content_text)

    return text

def main():
    filepath = "Fan made Shadowrun 7th Edition rules.md"
    try:
        with open(filepath, 'r') as f:
            text = f.read()

        print("Starting balancing...")
        text = balance_metatypes(text)
        text = balance_weapons(text)

        with open(filepath, 'w') as f:
            f.write(text)

        print("Balancing complete! The markdown file has been updated.")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
