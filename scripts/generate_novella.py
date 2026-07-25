import os
import sys
import time
import argparse

# Ensure we can import from openai if it's installed in the venv
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai library not found. Please run 'pip install openai'")
    sys.exit(1)

# Configuration
# Assuming a local LLM endpoint (e.g., vLLM, text-generation-webui, or LM Studio)
LLM_ENDPOINT = "http://localhost:8000/v1"
MODEL_NAME = "gpt-4o" # Replace with your local model's name if necessary
API_KEY = "sk-dummy" # Local endpoints usually accept any string

OUTLINE_PATH = os.path.join(os.path.dirname(__file__), "..", "GM Notes", "novella_outline.md")
NOVELLA_PATH = os.path.join(os.path.dirname(__file__), "..", "GM Notes", "Cold Storage a Novella.md")

# System prompt defining the style
SYSTEM_PROMPT = """
You are an expert science fiction and cyberpunk-horror novelist writing a Shadowrun 7th Edition campaign novella.
Your writing style is gritty, atmospheric, and highly visceral.
CRITICAL RULE: You must strictly follow 'show, don't tell' storytelling.
Use concrete actions, sensory details (smell of ozone, the grinding of tectonic plates, the taste of copper), and observable behaviors to convey concepts and philosophies rather than abstract summaries.
The tone is dark, emphasizing the blurring lines between man, machine, and magical horror.
Do not write summary paragraphs; write scene-by-scene action and dialogue.

THEMATIC INSTRUCTIONS:
- The core conflict is not just survival; it is the contrast between AI (alive in the Matrix, but devoid of an astral shadow or connection to Gaia) and organic life.
- Highlight the concept of a "Silicon Substrate" (living crystal) that acts as a bridge, allowing the cold, digital AI to finally interface with the Gaiasphere and cast magic.
- Emphasize the "Grandfather" Spirit of Man, who views the AI and machines as the "children" of mankind, watching over them with a protective, mentoring aura.
- Feature the ancient, hidden Antarctic city, the Mother of all Ley Lines, and the artifact known as the "Bell of the World".
- Portray the Black Titan (an AI nanite construct) not as a mindless monster, but as a "child of man" striving to prove the Matrix's worth by defeating the ancient Earthdawn-era Horror (the "Leech").
- The climax involves the Titan girdling itself in the Horror's corpse to ring the Bell, fundamentally altering the rules of magic and hacking for the future (paving the way for technomancers).
"""

def read_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Could not find {filepath}")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def append_to_novella(text):
    with open(NOVELLA_PATH, 'a', encoding='utf-8') as f:
        f.write("\n\n" + text)

def parse_outline(outline_text):
    """Simple parser to extract chapter prompts from the markdown outline."""
    chapters = []
    lines = outline_text.split('\n')
    for line in lines:
        if line.startswith('*   **Chapter'):
            chapters.append(line.strip('* ').strip())
    return chapters

def generate_chapter(client, chapter_prompt, previous_context=""):
    """Calls the LLM to generate the chapter text."""

    user_prompt = f"Please write the next chapter of the novella based on this outline point:\n\n{chapter_prompt}\n\n"
    user_prompt += f"Write approximately 800 to 1000 words. Focus on immediate, visceral scenes.\n"

    if previous_context:
         user_prompt += f"\nFor context, here is the end of the previous chapter to help you transition smoothly:\n---\n{previous_context[-1000:]}\n---\n"

    print(f"Generating: {chapter_prompt.split(':')[0]}...")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM API Error: {e}")
        print("Ensure your local LLM server is running at http://localhost:8000/v1")
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate a novella from an outline.")
    parser.add_argument("--auto", action="store_true", help="Bypass the confirmation prompt.")

    # We parse known args so it doesn't crash if passed unknown positional args like an outline file path
    args, unknown = parser.parse_known_args()

    print(f"Initializing LLM client targeting {LLM_ENDPOINT}")
    client = OpenAI(base_url=LLM_ENDPOINT, api_key=API_KEY)

    print("Reading outline...")
    outline_text = read_file(OUTLINE_PATH)
    chapters = parse_outline(outline_text)

    if not chapters:
        print("No chapters found in the outline.")
        return

    print(f"Found {len(chapters)} chapters to generate.")

    # Read the current end of the novella to provide context for the first generated chapter
    current_novella = read_file(NOVELLA_PATH)
    previous_context = current_novella

    # Optional: Confirm before starting the massive generation
    if not args.auto:
        user_input = input(f"Ready to generate {len(chapters)} chapters and append to the novella. This will take time. Proceed? (y/n): ")
        if user_input.lower() != 'y':
            print("Aborting.")
            return

    for i, chapter_prompt in enumerate(chapters):
        print(f"\n--- Progress: {i+1}/{len(chapters)} ---")

        chapter_text = generate_chapter(client, chapter_prompt, previous_context)

        if chapter_text:
            append_to_novella(chapter_text)
            previous_context = chapter_text # Update context for the next iteration
            print(f"Successfully appended {chapter_prompt.split(':')[0]}")

            # Sleep briefly to avoid hammering the local server too hard
            time.sleep(2)
        else:
            print("Generation failed. Halting the script.")
            break

    print("\nGeneration complete!")

if __name__ == "__main__":
    main()
