import re

with open("Fan made Shadowrun 7th Edition rules.tex", "r") as f:
    tex = f.read()

# We need to remove the text block duplicates of HK Caveat and Mauser Ladyline
# since their properly parsed gearitems are extracted at the bottom.

# Remove:
# \textbf{HK Caveat} (): A large framed H\&K pistol that can intimidating
# pass for a much heavier, more powerful, and dangerous weapon. Commonly
# carried by corp suits with more bark than bite.
tex = re.sub(r'\\textbf\{HK Caveat\}.*?more bark than bite\.', '', tex, flags=re.DOTALL)

# Remove:
# \textbf{Mauser Ladyline} (): An elegant pistol with a feminine design
# but suprising stopping power.
tex = re.sub(r'\\textbf\{Mauser Ladyline\}.*?stopping power\.', '', tex, flags=re.DOTALL)

# Clean up multiple empty lines
tex = re.sub(r'\n{3,}', '\n\n', tex)

with open("Fan made Shadowrun 7th Edition rules.tex", "w") as f:
    f.write(tex)
