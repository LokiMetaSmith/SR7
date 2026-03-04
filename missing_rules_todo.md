# Missing Rules TODO List

The following sections, headers, and descriptions in the Shadowrun 7th Edition rulebook (`rules.md`) were identified as incomplete or missing text:

## Sections & Categories
- [x] **Close Combat** \-
- [x] **Assault Rifles** \-
- [x] **Rocket Launchers** \-
- [x] **Rockets** \-
- [x] **Missile Launchers** \-
- [x] **Missiles** \-
- [x] **Flamethrowers** \-
- [x] **Special & Exotic Weapons** \-
- [x] **Vehicular Weaponry** \-
- [x] **Vehicular Rockets** \-
- [x] **Vehicular Missiles** \-
- [x] **Vehicular Torpedoes** \-

## Qualities & Mechanics
- [x] **Voice of Experience** \- 5 Karma (Meta Quality)
- [x] **Reactions:**
- [x] Truncated sentence under **Actions**: "e.g.; A character takes their Turn with*"

## Weapon Descriptions
- [x] **Ruger 100** (.308):
- [x] **HK G9A4z** (5.56):
- [x] **Ingram White Knight** ():
- [x] **Ruhrmetall GPRL-Alpha** ():

## Missing Weapon Stats & Incomplete Entries
- [ ] **Glock-Mini Giftzwerg** (Missing description and stats completely)
- [ ] **HK Caveat** (Incomplete stats table row)
- [ ] **Mauser Ladyline** (Incomplete stats table row)
- [ ] **Altmayr White Star** (Missing description and stats completely)
- [ ] **Glock Dragon Slayer** (Missing description and stats completely)
- [ ] **Luger Model 58** (Missing description and stats completely)
- [ ] **Mauser Gladiator** (Missing description and stats completely)
- [ ] **Walther Nova II** (Missing description and stats completely)
- [ ] **Walther P059 Futura** (Missing description and stats completely)
- [ ] **Ares Klapp MP** (Missing description and stats completely)
- [ ] **Steyr TMP-6** (Missing description and stats completely)
- [ ] **PJSS LNB/13** (Missing description and stats completely)
- [ ] **TEC 603 Bull** (Missing description and stats completely)

## Qualities Missing Karma Costs
- [ ] **Arcane Arrester** \- (Gnome Quality)
- [ ] **Built Tough** \- (Giant, Ogre, Ork, Physical, Troll, Satyr Quality)
- [ ] **Community Connection** \- (Ork, Troll Quality)
- [ ] **Dermal Deposits** \- (Troll Quality)
- [ ] **Fangs** \- (Hobgoblin Quality)
- [ ] **Galloping Stride** \- (Centaur Quality)
- [ ] **Hooves** \- (Centaur, Satyr Quality)
- [ ] **Low-Light Vision** \- (Centaur, Elf, Hobgoblin, Nocturna, Ogre, Ork, Satyr Quality)
- [ ] **Ogre Stomach** \- (Ogre Quality)
- [ ] **Reach (Positive)** \- (Giant, Elf, Ork, Troll Quality)
- [ ] **Satyr Legs** \- (Satyr Quality)
- [ ] **Thermographic Vision** \- (Dwarf, Gnome, Troll Quality)

## Tooling & Integration TODOs
- [ ] **analyze_rules.py Enhancements:** Add logic to detect weapon outliers (e.g. abnormally high/low DV vs Cost) and parse the rest of the weapon categories.
- [ ] **Chummer5a Custom XMLs:** Populate `custom_sr7e_qualities.xml` with the remaining 140+ custom qualities.
- [ ] **Chummer5a Custom XMLs:** Create `custom_sr7e_weapons.xml` with all parsed weapon stats from the rulebook.
- [ ] **Chummer5a Custom XMLs:** Create `custom_sr7e_metatypes.xml` with the custom Metatypes and their associated Karma costs.
- [ ] **Chummer5a Plugin C#:** Implement custom rule logic in `Shadowrun7EPlugin.cs` for features that XML data alone cannot support (e.g., custom Initiative rolling or specific rule variants).
