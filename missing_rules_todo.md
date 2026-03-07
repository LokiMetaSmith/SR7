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
- [x] **Glock-Mini Giftzwerg** (Missing description and stats completely)
- [x] **HK Caveat** (Incomplete stats table row)
- [x] **Mauser Ladyline** (Incomplete stats table row)
- [x] **Altmayr White Star** (Missing description and stats completely)
- [x] **Glock Dragon Slayer** (Missing description and stats completely)
- [x] **Luger Model 58** (Missing description and stats completely)
- [x] **Mauser Gladiator** (Missing description and stats completely)
- [x] **Walther Nova II** (Missing description and stats completely)
- [x] **Walther P059 Futura** (Missing description and stats completely)
- [x] **Ares Klapp MP** (Missing description and stats completely)
- [x] **Steyr TMP-6** (Missing description and stats completely)
- [x] **PJSS LNB/13** (Missing description and stats completely)
- [x] **TEC 603 Bull** (Missing description and stats completely)

## Qualities Missing Karma Costs
- [x] **Arcane Arrester** \- (Gnome Quality)
- [x] **Built Tough** \- (Giant, Ogre, Ork, Physical, Troll, Satyr Quality)
- [x] **Community Connection** \- (Ork, Troll Quality)
- [x] **Dermal Deposits** \- (Troll Quality)
- [x] **Fangs** \- (Hobgoblin Quality)
- [x] **Galloping Stride** \- (Centaur Quality)
- [x] **Hooves** \- (Centaur, Satyr Quality)
- [x] **Low-Light Vision** \- (Centaur, Elf, Hobgoblin, Nocturna, Ogre, Ork, Satyr Quality)
- [x] **Ogre Stomach** \- (Ogre Quality)
- [x] **Reach (Positive)** \- (Giant, Elf, Ork, Troll Quality)
- [x] **Satyr Legs** \- (Satyr Quality)
- [x] **Thermographic Vision** \- (Dwarf, Gnome, Troll Quality)

## Tooling & Integration TODOs
- [x] **analyze_rules.py Enhancements:** Add logic to detect weapon outliers (e.g. abnormally high/low DV vs Cost) and parse the rest of the weapon categories.
- [x] **Chummer5a Custom XMLs:** Populate `custom_sr7e_qualities.xml` with the remaining 140+ custom qualities.
- [x] **Chummer5a Custom XMLs:** Create `custom_sr7e_weapons.xml` with all parsed weapon stats from the rulebook.
- [x] **Chummer5a Custom XMLs:** Create `custom_sr7e_metatypes.xml` with the custom Metatypes and their associated Karma costs.
- [x] **Chummer5a Plugin C#:** Implement custom rule logic in `Shadowrun7EPlugin.cs` for features that XML data alone cannot support (e.g., custom Initiative rolling or specific rule variants).
