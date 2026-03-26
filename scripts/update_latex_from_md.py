import argparse
import re
from markdown_it import MarkdownIt

def parse_markdown(text):
    md = MarkdownIt("commonmark").enable("table")
    return md.parse(text)

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
        elif token.type == "th_open" or token.type == "td_open":
            current_cell = ""
        elif token.type == "inline" and in_table:
            current_cell = token.content
        elif token.type == "th_close":
            headers.append(current_cell)
        elif token.type == "td_close":
            current_row.append(current_cell)
        elif token.type == "tr_close":
            if current_row:
                current_table_rows.append(current_row)
                current_row = []
        elif token.type == "table_close":
            in_table = False
            tables.append((headers, current_table_rows))

    return tables

def escape_latex(text):
    text = text.replace("\\&", "&")
    text = text.replace("&", r"\&")
    text = text.replace("%", r"\%")
    text = text.replace("$", r"\$")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    # text = text.replace("¥", r"\xa5")
    # Replace markdown bold with latex bold
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    # Replace markdown italic with latex emph
    text = re.sub(r'\*(.*?)\*', r'\\emph{\1}', text)
    return text

def normalize_text(text):
    text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text)
    text = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    return text

def main():
    parser = argparse.ArgumentParser(description="Update LaTeX tables from Markdown source.")
    parser.add_argument("--md", default="Fan made Shadowrun 7th Edition rules.md", help="Path to markdown file")
    parser.add_argument("--tex", default="Fan made Shadowrun 7th Edition rules.tex", help="Path to latex file")
    args = parser.parse_args()

    with open(args.md, 'r', encoding='utf-8') as f:
        md_content = f.read()

    with open(args.tex, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    tokens = parse_markdown(md_content)
    tables = extract_tables(tokens)
    print(f"Found {len(tables)} tables in Markdown.")

    # Find all longtables in LaTeX
    lt_pattern = re.compile(r'\\begin\{longtable\}\[\]\{@\{\}(.*?)\\endhead\s*\\bottomrule\\noalign\{\}\s*\\endlastfoot\n(.*?)(\\end\{longtable\})', re.DOTALL)

    def replacer(match):
        header_def = match.group(1)
        body = match.group(2)
        end_tag = match.group(3)

        # Extract headers from the LaTeX header definition to match against Markdown tables
        # Headers in LaTeX usually look like \begin{minipage}[b]{\linewidth}\raggedright Header \end{minipage}
        tex_headers = re.findall(r'\\begin\{minipage\}.*?\\raggedright\s*(.*?)\s*\\end\{minipage\}', header_def, re.DOTALL)
        if not tex_headers:
            # Maybe they are plain headers
            lines = header_def.split('\\midrule')[0].split('\n')
            last_line = lines[-2] if len(lines) >= 2 else lines[-1]
            tex_headers = [x.strip() for x in last_line.split('&')]

        normalized_tex_headers = [normalize_text(h) for h in tex_headers]

        # Find the matching markdown table
        best_match = None
        for headers, rows in tables:
            normalized_md_headers = [normalize_text(h) for h in headers]
            if normalized_md_headers == normalized_tex_headers:
                best_match = rows
                break

        if best_match:
            # Build new latex body
            new_body = ""
            for row in best_match:
                escaped_row = [escape_latex(c) for c in row]
                new_body += " & ".join(escaped_row) + r" \\" + "\n"
            return r"\begin{longtable}[]{@{}" + header_def + r"\endhead" + "\n" + r"\bottomrule\noalign{}" + "\n" + r"\endlastfoot" + "\n" + new_body + end_tag

        # If no match, return original
        return match.group(0)

    new_tex_content = lt_pattern.sub(replacer, tex_content)

    if new_tex_content != tex_content:
        with open(args.tex, 'w', encoding='utf-8') as f:
            f.write(new_tex_content)
        print("Updated LaTeX file successfully!")
    else:
        print("No changes made. Either tables already match or couldn't find matching headers.")

if __name__ == "__main__":
    main()
