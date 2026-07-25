import argparse
import json
import os
from datetime import datetime

def get_db_file(story_name):
    # Ensure it's saved in the specific campaign folder
    base_dir = os.path.join(os.path.dirname(__file__), "..", "campaigns", story_name)
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "continuity.jsonl")

def init_db(story_name):
    db_file = get_db_file(story_name)
    if not os.path.exists(db_file):
        with open(db_file, 'w', encoding='utf-8') as f:
            pass

def add_fact(story_name, entity, category, fact, source="manual"):
    db_file = get_db_file(story_name)
    record = {
        "timestamp": datetime.now().isoformat(),
        "entity": entity,
        "category": category,
        "fact": fact,
        "source": source
    }
    with open(db_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
    print(f"Added fact for '{entity}' in story '{story_name}' (Category '{category}'): {fact}")

def remove_fact(story_name, entity, fact_substring):
    db_file = get_db_file(story_name)
    records = []
    removed = 0
    with open(db_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                record = json.loads(line)
                if record['entity'] == entity and fact_substring.lower() in record['fact'].lower():
                    removed += 1
                    continue
                records.append(line)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON line: {line.strip()}")
                records.append(line)

    if removed > 0:
        with open(db_file, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(r)
        print(f"Removed {removed} fact(s) for '{entity}' in story '{story_name}' matching '{fact_substring}'.")
    else:
        print(f"No facts found for '{entity}' in story '{story_name}' matching '{fact_substring}'.")

def list_facts(story_name, entity=None, category=None):
    db_file = get_db_file(story_name)
    count = 0

    if not os.path.exists(db_file):
        print(f"No facts found for story '{story_name}'.")
        return

    with open(db_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                record = json.loads(line)
                if entity and record['entity'] != entity:
                    continue
                if category and record['category'] != category:
                    continue
                print(f"[{record['category']}] {record['entity']}: {record['fact']} (Source: {record.get('source', 'unknown')})")
                count += 1
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON line: {line.strip()}")

    if count == 0:
        print("No matching facts found.")


def main():
    parser = argparse.ArgumentParser(description="Continuity Tracker for Narrative Generation")
    parser.add_argument("--story", required=True, help="The name of the story/campaign (e.g., 'cold_storage')")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    parser_add = subparsers.add_parser("add", help="Add a new fact to the continuity matrix")
    parser_add.add_argument("entity", help="The character, location, or item (e.g., 'Sammy', 'Tar Creek')")
    parser_add.add_argument("category", help="The type of fact (e.g., 'Appearance', 'Background', 'Plot Thread')")
    parser_add.add_argument("fact", help="The specific detail or fact to record")
    parser_add.add_argument("--source", default="manual", help="The source of the fact (e.g., 'Chapter 3')")

    # Remove command
    parser_remove = subparsers.add_parser("remove", help="Remove a fact from the continuity matrix")
    parser_remove.add_argument("entity", help="The entity the fact belongs to")
    parser_remove.add_argument("fact_substring", help="A substring of the fact to match and remove")

    # List command
    parser_list = subparsers.add_parser("list", help="List facts from the continuity matrix")
    parser_list.add_argument("--entity", help="Filter by entity")
    parser_list.add_argument("--category", help="Filter by category")

    args = parser.parse_args()
    init_db(args.story)

    if args.command == "add":
        add_fact(args.story, args.entity, args.category, args.fact, args.source)
    elif args.command == "remove":
        remove_fact(args.story, args.entity, args.fact_substring)
    elif args.command == "list":
        list_facts(args.story, args.entity, args.category)

if __name__ == "__main__":
    main()
