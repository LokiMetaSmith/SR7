import re
import argparse
from pathlib import Path

# Define regular expressions for LLM smells
SMELLS = {
    "x_is_the_y_of_z": re.compile(r"\b(\w+(?:\s+\w+){0,3})\s+is\s+the\s+(\w+(?:\s+\w+){0,3})\s+of\s+(\w+(?:\s+\w+){0,3})\b", re.IGNORECASE),
    "not_just_x_its_y": re.compile(r"\bnot\s+(?:just|merely|only)\s+(.+?),\s*(?:but\s+also|it['\u2019]s|its)\s+(.+?)\b", re.IGNORECASE),
    "consecutive_short_sentences": re.compile(r"([A-Z][^.!?]{10,40}[.!?])\s+([A-Z][^.!?]{10,40}[.!?])\s+([A-Z][^.!?]{10,40}[.!?])"),
    "excessive_em_dashes": re.compile(r"(?:---|—|–)"),
    "punchline_endings": re.compile(r"[.!?]\s+([A-Z][^.!?]{10,50}[.!?])\s*\n"),
    "llm_buzzwords": re.compile(r"\b(delve|tapestry|testament|navigate|realm|landscape|intricate|nuanced|multifaceted)\b", re.IGNORECASE),
    "repetitive_openings": re.compile(r"^(?:The next morning|Later that day|Suddenly|In the end|Afterwards|A few hours later|The following day)[,\s]", re.IGNORECASE)
}

def check_file(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    for i, line in enumerate(lines):
        for smell_name, regex in SMELLS.items():
            if smell_name == "excessive_em_dashes":
                dash_count = len(regex.findall(line))
                if dash_count > 2:
                    results.append((i + 1, smell_name, line.strip(), f"Found {dash_count} em-dashes"))
            elif smell_name in ("consecutive_short_sentences", "punchline_endings"):
                # These are checked at the paragraph level below
                pass
            else:
                matches = regex.findall(line)
                if matches:
                    results.append((i + 1, smell_name, line.strip(), str(matches)))

    paragraphs = content.split('\n\n')
    line_offset = 1
    for p in paragraphs:
        if SMELLS["consecutive_short_sentences"].search(p):
            results.append((line_offset, "consecutive_short_sentences", p[:100] + "...", "Found 3+ consecutive short sentences"))

        opening_match = SMELLS["repetitive_openings"].search(p.strip())
        if opening_match:
            results.append((line_offset, "repetitive_openings", p[:50] + "...", f"Found repetitive/generic opening: '{opening_match.group(0).strip()}'"))

        # Lexical variety check (detect simple repetitive phrasing in the same paragraph)
        # We look for repeated adjective+noun or similar 3-4 word phrases
        words = re.findall(r'\b[a-zA-Z]{4,}\b', p.lower())
        if len(words) > 10:
            ngrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
            seen = set()
            for ngram in ngrams:
                if ngram in seen:
                    results.append((line_offset, "lexical_repetition", ngram, f"Found repeated 3-word phrase within paragraph: '{ngram}'"))
                seen.add(ngram)

        sentences = re.split(r'[.!?]+', p.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) > 2:
            last_sentence = sentences[-1]
            if 5 < len(last_sentence) < 40 and not last_sentence.startswith(("-", "*", "#")):
                prev_sentence = sentences[-2]
                if len(prev_sentence) > 60:
                   results.append((line_offset, "punchline_ending", last_sentence, f"Paragraph ends with a short punchline sentence: '{last_sentence}'"))

        line_offset += p.count('\n') + 2

    return sorted(results, key=lambda x: x[0])


def main():
    parser = argparse.ArgumentParser(description="Lint markdown files for LLM writing smells.")
    parser.add_argument("path", help="File or directory to lint")
    args = parser.parse_args()

    target_path = Path(args.path)
    files_to_check = []

    if target_path.is_file():
        files_to_check.append(target_path)
    elif target_path.is_dir():
        files_to_check.extend(list(target_path.rglob("*.md")))

    total_issues = 0
    for file_path in files_to_check:
        issues = check_file(file_path)
        if issues:
            print(f"\n--- {file_path} ---")
            for line_num, smell, text, details in issues:
                print(f"Line {line_num} | {smell}: {details}")
                total_issues += 1

    print(f"\nTotal issues found: {total_issues}")


if __name__ == "__main__":
    main()
