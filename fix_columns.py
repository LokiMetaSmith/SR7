import re

with open("Fan made Shadowrun 7th Edition rules.tex", "r") as f:
    tex = f.read()

# Current colspec: colspec = {X[1.5,l] *{10}{X[c]}}
# We want:
# 1 Name -> X[2.5,l]
# 2 ACC -> X[0.5,c]
# 3 DV -> X[0.5,c]
# 4 AP -> X[0.5,c]
# 5 MODE -> X[c]
# 6 RC -> X[0.5,c]
# 7 RANGE -> X[c]
# 8 AMMO -> X[c]
# 9 AVAIL -> X[c]
# 10 WEIGHT -> X[c]
# 11 COST -> X[c]

new_colspec = r"colspec = {X[2.5,l] X[0.5,c] X[0.5,c] X[0.5,c] X[c] X[0.5,c] X[c] X[c] X[c] X[c] X[c]}"
tex = tex.replace(r"colspec = {X[1.5,l] *{10}{X[c]}}", new_colspec)

with open("Fan made Shadowrun 7th Edition rules.tex", "w") as f:
    f.write(tex)
