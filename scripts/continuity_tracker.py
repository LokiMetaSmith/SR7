import argparse
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "continuity.jsonl")

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            pass

def add_fact(entity, category, fact, source="manual"):
    record = {
        "timestamp": datetime.now().isoformat(),
        "entity": entity,
        "category": category,
        "fact": fact,
        "source": source
    }
    with open(DB_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
    print(f"Added fact for '{entity}' in category '{category}': {fact}")

def remove_fact(entity, fact_substring):
    records = []
    removed = 0
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            if record['entity'] == entity and fact_substring.lower() in record['fact'].lower():
                removed += 1
                continue
            records.append(line)

    if removed > 0:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(r)
        print(f"Removed {removed} fact(s) for '{entity}' matching '{fact_substring}'.")
    else:
        print(f"No facts found for '{entity}' matching '{fact_substring}'.")

def list_facts(entity=None, category=None):
    count = 0
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            if entity and record['entity'] != entity:
                continue
            if category and record['category'] != category:
                continue
            print(f"[{record['category']}] {record['entity']}: {record['fact']} (Source: {record.get('source', 'unknown')})")
            count += 1
    if count == 0:
        print("No matching facts found.")


def main():
    parser = argparse.ArgumentParser(description="Continuity Tracker for Narrative Generation")
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
    init_db()

    if args.command == "add":
        add_fact(args.entity, args.category, args.fact, args.source)
    elif args.command == "remove":
        remove_fact(args.entity, args.fact_substring)
    elif args.command == "list":
        list_facts(args.entity, args.category)

if __name__ == "__main__":
    main()
