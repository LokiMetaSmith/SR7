# AI Agent Guidelines

## General Coding Rules
* Ensure that the game engine, maps, and campaigns are built strictly modular. Avoid hardcoding campaign data in UI components or engine logic.
* The `AGENTS.md` file should include programmatic checks if any exist in the future.

## Narrative and Lore Writing Guidelines
When writing lore, character descriptions, campaign narratives, or any text generation, strictly follow 'show, don't tell' storytelling. Use concrete actions, sensory details, and observable behaviors to convey concepts and philosophies rather than abstract summaries.

### Avoiding "LLM Smells"
Based on common AI-generated text patterns, AIs must actively avoid the following stylistic clichés in their writing:
1. **Way too many punchlines:** Avoid ending every paragraph with a dramatic, punchy, or overly philosophical one-liner (e.g., "Symmetry becomes a trap.").
2. **Consecutive short sentences:** Do not use staccato, repetitive short sentences to artificially create tension (e.g., "Yet the tilt is not an accident. It is the shape of the optimum."). Vary sentence length naturally.
3. **"X is the Y of Z" formula:** Avoid this specific metaphor structure (e.g., "Cringe is the visible signature of moving along a gradient you chose."). Find more organic ways to explain relationships.
4. **"It's not just X, it's Y" formula:** Avoid this escalating structure (e.g., "solutions that do not merely satisfy the constraint but satisfy the aesthetic instincts").
5. **Excessive em-dashes:** Use em-dashes sparingly. Do not use them as a crutch for sentence structure.
6. **"Delve", "tapestry", "testament", etc.:** Avoid classic LLM buzzwords.
7. **Lexical Repetition:** Avoid using the same descriptors, metaphors, or specific phrasing repeatedly across scenes or chapters. Rotate vocabulary dynamically.
8. **Monotonous Tension (Tension Matrix):** Characters in a relationship must not re-litigate the same single point of conflict in every shared scene. Rotate different 'seams' of tension (e.g., ambition, faith, silence, trust) across scenes to create multi-dimensional relationships.
9. **Repetitive Chapter/Scene Openings & Endings:** Do not start multiple scenes/chapters with time-skips or generic transitions (e.g., "The next morning," "Later that day"). Rotate opening techniques (sensory immersion, action, dialogue cold open, etc.) and ending techniques (image, question, emotional beat, action mid-motion).

### Continuity Tracking
To avoid continuity slip-ups (e.g., a character changing eye color mid-book, or a dropped plot thread), use the `scripts/continuity_tracker.py` script.
* **Record Facts:** When establishing a new, permanent fact about a character, location, or plot thread in generated text, call `python scripts/continuity_tracker.py --story "<story_name>" add "<Entity>" "<Category>" "<Fact>" --source "<Source>"`.
* **Verify Facts:** Before generating a new scene, query existing facts to ensure consistency by running `python scripts/continuity_tracker.py --story "<story_name>" list --entity "<Entity>"`.
* Examples of categories: "Appearance", "Background", "Plot Thread", "Relationship".

Prioritize natural, varied, and grounded writing over overly dramatic or formulaic structures.
