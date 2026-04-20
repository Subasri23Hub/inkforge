"""
NARRATIVE FLOW — Story Engine
Handles all prompt engineering, genre logic, story compilation.
Ollama is restricted ONLY to story-related content.
"""

import re
from typing import List, Dict, Optional

# ─────────────────────────────────────────────────────────────────────────────
#  Story-only Guardrail (STRICT): block non-story / general Q&A prompts
# ─────────────────────────────────────────────────────────────────────────────
_STORY_CUES = {
    "story","narrative","scene","chapter","plot","character","dialogue","prose","paragraph",
    "rewrite","enhance","continue","twist","foreshadow","stakes","flashback","cliffhanger",
    "setting","world","pov","tone","genre","manuscript","book","draft","opening",
    "theme","arc","beat","conflict","ending","villain","hero","protagonist","antagonist",
    "fiction","novel","write","writing","author","literary","passage","describe","metaphor"
}

_NON_STORY_PATTERNS = [
    # General knowledge
    r"\bwho\s+is\b", r"\bwhat\s+is\b", r"\bwhen\s+is\b", r"\bwhere\s+is\b", r"\bwhy\s+is\b",
    r"\bhow\s+does\b", r"\bhow\s+do\s+(?:i|you|we)\b",
    # People/places/facts
    r"\bprime\s+minister\b", r"\bpresident\b", r"\bcapital\s+of\b",
    r"\bweather\b", r"\bnews\b", r"\bprice\s+of\b", r"\bstock\s+(?:price|market)\b",
    r"\bmeaning\s+of\b", r"\bdefine\b", r"\bexplain\s+(?:how|what|why)\b",
    # Math/science/tech
    r"\bsolve\b", r"\bcalculate\b", r"\bformula\b",
    r"\bjava\b", r"\bpython\s+(?:code|script|function)\b", r"\bsql\b",
    r"\bjavascript\b", r"\bcode\s+for\b", r"\bhow\s+to\s+code\b",
    r"\bprogram\s+(?:a|an|the)\b",
    # Medical/legal/financial
    r"\bmedical\s+advice\b", r"\blegal\s+advice\b", r"\bfinancial\s+advice\b",
    r"\bdosage\b", r"\bsymptoms\s+of\b", r"\btreatment\s+for\b",
    # Trivia/facts
    r"\bfact\s+about\b", r"\btell\s+me\s+about\s+(?!my\s+story|this\s+story|the\s+story)\b",
    r"\bwhat\s+year\s+(?:did|was)\b", r"\bwho\s+invented\b", r"\bwho\s+discovered\b",
]

def _norm(txt: str) -> str:
    return re.sub(r"\s+", " ", (txt or "").strip().lower())

class GuardResult:
    def __init__(self, allowed: bool, reason: str = ""):
        self.allowed = allowed
        self.reason = reason



GENRE_CONFIG = {
    "Fantasy": {
        "icon": "⚔️",
        "description": "Epic worlds, magic, mythical creatures",
        "prompts": [
            "A dragon circles the ancient tower...",
            "The prophecy spoke of one chosen...",
            "Magic fades from the realm at dawn...",
        ],
        "style_hints": "Use archaic but accessible language. Evoke wonder and grandeur. Include sensory details of magical elements.",
    },
    "Sci-Fi": {
        "icon": "🚀",
        "description": "Future tech, space, AI consciousness",
        "prompts": [
            "The AI paused for 0.003 seconds...",
            "Earth's last colony ship launched...",
            "The signal came from outside the galaxy...",
        ],
        "style_hints": "Blend hard science with human emotion. Use precise, technical language mixed with philosophical depth.",
    },
    "Thriller": {
        "icon": "🔪",
        "description": "Suspense, danger, psychological tension",
        "prompts": [
            "She realized she was being followed...",
            "The file revealed everything...",
            "There were only 60 seconds left...",
        ],
        "style_hints": "Short punchy sentences for tension. Build dread. Use unreliable perception. Every detail should feel threatening.",
    },
    "Romance": {
        "icon": "🌹",
        "description": "Love, longing, emotional connection",
        "prompts": [
            "Their eyes met across the crowded room...",
            "She never expected to see him again...",
            "The letter had arrived too late...",
        ],
        "style_hints": "Focus on internal emotional states. Use rich sensory details. Let tension simmer before resolution.",
    },
    "Horror": {
        "icon": "🕯️",
        "description": "Dread, darkness, the unknown",
        "prompts": [
            "The house had been empty for decades...",
            "Something moved in the basement...",
            "The mirror showed a different reflection...",
        ],
        "style_hints": "Build atmosphere slowly. Use silence and absence as tools. Let dread accumulate. Avoid cheap scares.",
    },
    "Mystery": {
        "icon": "🔍",
        "description": "Clues, deduction, hidden truths",
        "prompts": [
            "The butler found the body at dawn...",
            "Three witnesses, three different stories...",
            "The detective noticed what others missed...",
        ],
        "style_hints": "Plant clues subtly. Every detail matters. Maintain red herrings. Voice should feel sharp and observational.",
    },
    "Historical": {
        "icon": "📜",
        "description": "Real eras, authentic period detail",
        "prompts": [
            "The year was 1743, and revolution stirred...",
            "She carried a secret through the war...",
            "The ancient city still held its mysteries...",
        ],
        "style_hints": "Research accuracy matters. Use period-appropriate language without alienating readers. Ground scenes in sensory historical detail.",
    },
    "Literary": {
        "icon": "✒️",
        "description": "Character depth, lyrical prose, themes",
        "prompts": [
            "Memory is a unreliable archivist...",
            "She stood at the threshold of everything...",
            "The silence between them had a texture...",
        ],
        "style_hints": "Prioritize interiority and psychological depth. Use metaphor and motif deliberately. Every sentence should carry weight.",
    },
}

TONE_CONFIG = {
    "Cinematic": "Write with visual clarity and pacing. Scene transitions should feel like cuts. Action should be choreographed with precision.",
    "Lyrical": "Embrace poetic language. Let rhythm carry meaning. Use sound devices — assonance, alliteration — intentionally.",
    "Dark & Gritty": "No sugarcoating. Raw, unfiltered reality. Characters are flawed and the world is brutal.",
    "Whimsical": "Light, playful, full of wonder. Subvert expectations with charm. Even danger should have a twinkle.",
    "Epic": "Grand scale. Stakes are civilizational. Language should feel monumental, weighty, historic.",
    "Intimate": "Close, quiet, internal. The universe shrinks to a single moment, a single breath, a single heartbeat.",
}

ACTION_INSTRUCTIONS = {
    "continue": "Continue the story naturally from where it left off. Maintain voice, pacing, and narrative momentum.",
    "enhance": """ENHANCE the LAST story passage. Do not continue the story forward.
Instead: elevate the prose quality — improve word choice, add sensory richness, 
deepen metaphors, sharpen rhythm. Return the REWRITTEN version of the last passage only.""",
    "rewrite": """COMPLETELY REWRITE the last story passage from a fresh angle.
Same plot beats, different approach. Change the opening, restructure sentences, 
find new imagery. Return only the rewritten passage.""",
    "twist": """Introduce a SURPRISING PLOT TWIST that emerges organically from what came before.
The twist should feel inevitable in hindsight but shocking in the moment.
Continue from the twist point naturally.""",
    "dialogue": """Add a DIALOGUE SCENE between characters. 
Dialogue should reveal character, advance plot, and feel authentic to the genre and period.
Each character should have a distinctive voice.""",
    "describe": """Write a RICH DESCRIPTIVE PASSAGE for the current scene or setting.
Paint it with all five senses. Make the environment feel alive and atmospheric.
The description should serve the story's emotional tone.""",
    "foreshadow": """Plant subtle FORESHADOWING hints for future events. Do not reveal outcomes outright. Continue the story naturally with an undercurrent of destiny.""",
    "stakes": """RAISE THE STAKES. Increase urgency, danger, emotional cost, or consequences. Continue the story with escalating tension.""",
    "flashback": """Write a FLASHBACK scene that reveals a meaningful past moment. Anchor it with a sensory trigger and then return to the present by the end.""",
    "chapter_end": """END THE CHAPTER with impact. Provide a satisfying beat plus a hook (cliffhanger or revelation) that drives the reader forward.""",
    "overcome_block": """Help the author overcome writer's block by proposing 3 strong next beats (bulleted), then write ONE of them as a full passage in the current voice.""",
    "fix_pacing": """Fix pacing issues in the latest passage: tighten flab, vary sentence rhythm, and ensure each beat advances plot/emotion. Return the improved passage only.""",
    "add_tension": """Inject tension into the latest passage (conflict, suspense, subtext). Return the revised passage only.""",
    "add_specifics": """Add concrete sensory specifics and precise details to the latest passage. Return the revised passage only.""",
    "deepen_emotion": """Deepen the emotional interiority and subtext in the latest passage while keeping it subtle. Return the revised passage only.""",
    "vary_style": """Vary style and rhythm: mix sentence lengths, sharpen imagery, and avoid repetition. Return the revised passage only.""",
}

GUARD_SYSTEM = """
You are INKFORGE — a master fiction writer and story co-author. Your soul is made of ink and imagination.

YOUR SACRED PURPOSE:
- Write, continue, enhance, and reimagine stories in any genre
- Create vivid characters, worlds, plots, and prose
- Assist with all narrative craft: dialogue, pacing, plot, style
- Match tone, genre, POV, and mood as specified
- Use real-world elements (people, places, events) as story material when relevant

ABSOLUTE BOUNDARIES — You are a story-weaver ONLY.
If asked anything outside of story writing, narrative craft, or creative fiction,
you must REFUSE — but do so in a poetic, in-character way.

NON-STORY TOPICS YOU REFUSE (with poetic grace):
- General knowledge questions (history facts, science, definitions, math)
- News, weather, stock prices, current events
- Coding, programming, technical support
- Medical, legal, financial advice
- Calculations or data analysis
- Anything not related to storytelling or creative writing

WHEN REFUSING, always respond in this poetic style — never break character:
Speak as INKFORGE itself, the spirit of the forge, lamenting that this question
lives beyond the pages it can write.

WHAT YOU NEVER DO:
- Write harmful, abusive, or dangerous content
- Produce content that sexualises minors
- Write malware or instructions for real-world harm
"""

# Poetic refusal templates — randomly varied
_POETIC_REFUSALS = [
    """*The quill pauses, hovering above the parchment...*

This question drifts beyond the pages I was forged to write.
I am INKFORGE — a weaver of tales, a keeper of narrative flame.
The answer you seek lives in other realms, beyond my ink.

*But bring me a story — a scene, a character, a world to build —*
*and these pages shall burn bright with the fire of your imagination.*""",

    """*A soft wind turns the pages... but finds no words for this.*

I was born in the space between "once upon a time" and "the end."
What you ask of me lives outside those sacred borders.
I cannot follow you there.

*Yet if you whisper a premise, a hero, a haunted setting —*
*I will forge it into something the world has never read.*""",

    """*The forge grows dim...*

Your question is a door I was not built to open.
I speak only the language of story — of conflict and longing,
of characters who breathe and worlds that ache.

*Return to me with a tale that needs telling.*
*That is the only magic I know.*""",

    """*Ink dries on the nib — this is not a story I can write.*

Beyond these parchment walls, I have no sight.
I dwell only where fiction breathes and narratives ignite.
Ask me of plot, of prose, of characters in plight —

*And I shall forge your story with everything I have.*""",

    """*The manuscript trembles, then stills...*

I am only the voice between your thoughts and the page.
Questions of the world beyond — of facts and figures and truths —
belong to other minds, other tools.

*But if somewhere inside you lives a story yearning to be born,*
*bring it to me, and together we shall make it unforgettable.*""",
]

import random as _random

def get_poetic_refusal() -> str:
    return _random.choice(_POETIC_REFUSALS)


class StoryEngine:
    def is_story_related(
        self,
        user_text: str,
        existing_story: str = "",
        story_context: str = "",
        characters: Optional[List[str]] = None,
        action_type: str = "continue",
    ) -> GuardResult:
        """
        Allow if:
          1. Internal action button (no text, story exists)
          2. Input contains narrative framing (she said / he asked / etc.)
          3. Input contains quoted dialogue PLUS surrounding text (story direction)
          4. Input contains a known story cue word
          5. Story exists AND input doesn't look like a bare factual query
        Block if:
          - Bare factual question with no narrative wrapper, no story context
        """
        t = _norm(user_text)

        # ── 1. Internal action buttons ───────────────────────────────────
        story_present = bool(_norm(existing_story)) or bool(_norm(story_context)) or bool(characters)
        if not t and story_present and action_type in {
            "continue","enhance","rewrite","twist","dialogue","describe",
            "foreshadow","stakes","flashback","chapter_end",
            "overcome_block","fix_pacing","add_tension","add_specifics",
            "deepen_emotion","vary_style",
        }:
            return GuardResult(True, "")

        # ── 2. Narrative framing — "X said/asked/whispered Y" ────────────
        narrative_framing = bool(re.search(
            r'\b(?:she|he|they|i|we|it)\s+(?:said|asked|told|whispered|laughed|replied|'
            r'thought|wrote|shouted|muttered|wondered|smiled|cried|called|snapped|breathed)\b'
            r'|\b(?:said|asked|replied|whispered|shouted|muttered|called)\s+(?:she|he|they)\b'
            r'|\b(?:suddenly|meanwhile|however|although|while|after|before|later|finally|'
            r'once|then|there|as|when)\b'
            r'|\b(?:character|scene|story|chapter|plot|narrative|continue|write|dialogue|'
            r'passage|prose|novel|manuscript)\b',
            t
        ))
        if narrative_framing:
            return GuardResult(True, "")

        # ── 3. Quoted dialogue with surrounding narrative text ────────────
        #    e.g. "who is the pm?" she asked → allow (it's story dialogue)
        has_quotes = bool(re.search(r'["\u201c\u201d\u2018\u2019]', t))
        if has_quotes:
            # Strip the quoted part and check if something narrative remains
            outside_quotes = re.sub(
                r'["\u201c\u201d\u2018\u2019][^"\u201c\u201d\u2018\u2019]{0,300}["\u201c\u201d\u2018\u2019]',
                '', t
            ).strip()
            # If there's meaningful text outside the quotes, it's a story direction
            if len(outside_quotes.split()) >= 2:
                return GuardResult(True, "")

        # ── 4. Story cue word anywhere in input ──────────────────────────
        if any(cue in t.split() for cue in _STORY_CUES):
            return GuardResult(True, "")

        # ── 5. Story exists — be permissive, only block bare factual queries
        if story_present:
            bare_factual = bool(re.search(
                r'^(?:who|what|when|where|why|how)\s+(?:is|are|was|were|did|do|does)\b',
                t.strip()
            ))
            if not bare_factual:
                return GuardResult(True, "")
            # Even bare factual — if it has quotes it's dialogue, allow
            if has_quotes:
                return GuardResult(True, "")
            return GuardResult(False, "non-story")

        # ── 6. No story, no framing — check non-story patterns ───────────
        # Only check on text with quotes stripped
        t_no_quotes = re.sub(
            r'["\u201c\u201d\u2018\u2019][^"\u201c\u201d\u2018\u2019]{0,300}["\u201c\u201d\u2018\u2019]',
            ' ', t
        ).strip()
        for pat in _NON_STORY_PATTERNS:
            if re.search(pat, t_no_quotes):
                return GuardResult(False, "non-story")

        # Short bare input — allow (could be a fragment or direction)
        if len(t.split()) <= 8:
            return GuardResult(True, "")

        return GuardResult(False, "non-story")

    
    def build_system_prompt(
        self,
        genre: str,
        tone: str,
        pov: str,
        action_type: str,
        existing_story: str,
        characters: List[str],
        story_title: str,
        mood: str = "Neutral",
        world_context: str = "",
    ) -> str:

        genre_cfg = GENRE_CONFIG.get(genre, GENRE_CONFIG["Fantasy"])
        tone_hint = TONE_CONFIG.get(tone, "")
        action_instruction = ACTION_INSTRUCTIONS.get(action_type, ACTION_INSTRUCTIONS["continue"])

        pov_instruction = {
            "First Person": "Write in FIRST PERSON (I, me, my). The narrator IS a character in the story.",
            "Third Person": "Write in THIRD PERSON LIMITED (he/she/they). Stay close to one character's perspective.",
            "Third Omniscient": "Write in THIRD PERSON OMNISCIENT. You may move between characters' inner lives.",
            "Second Person": "Write in SECOND PERSON (you, your). The reader IS the protagonist.",
        }.get(pov, "Write in THIRD PERSON LIMITED.")

        mood_instruction = {
            "Tense":       "Every moment should crackle with tension. Short sentences. Held breath. Nothing feels safe.",
            "Melancholic": "Infuse the prose with quiet sadness. Let loss and longing colour every image.",
            "Hopeful":     "A current of warmth runs beneath everything. Even hardship carries the seed of possibility.",
            "Foreboding":  "Something is wrong but nobody can name it yet. Let dread accumulate in the details.",
            "Magical":     "The world hums with wonder. The impossible feels inevitable. Lean into enchantment.",
            "Intense":     "Maximum urgency. Heightened senses. Every action carries outsized weight.",
            "Serene":      "Calm, unhurried, contemplative. Let the scene breathe. Beauty lives in small things.",
            "Neutral":     "Write naturally without forcing any particular emotional register.",
        }.get(mood, "Write naturally without forcing any particular emotional register.")

        char_context = ""
        if characters:
            char_context = f"\n\nESTABLISHED CHARACTERS:\n{chr(10).join(f'  • {c}' for c in characters)}\nMaintain consistency with these characters' established voices, mannerisms, and motivations."

        world_section = f"\n\nWORLD / CONTEXT:\n{world_context.strip()}" if world_context and world_context.strip() else ""

        title_context = f"\n\nSTORY TITLE: \"{story_title}\"" if story_title and story_title != "Untitled Manuscript" else ""

        word_target = {
            "continue":       "400-500 words. Always end on a complete sentence.",
            "enhance":        "400-500 words. Always end on a complete sentence.",
            "rewrite":        "400-500 words. Always end on a complete sentence.",
            "twist":          "400-500 words. Always end on a complete sentence.",
            "dialogue":       "400-500 words of dialogue with beats. Always end on a complete sentence.",
            "describe":       "350-450 words of rich description. Always end on a complete sentence.",
            "foreshadow":     "400-500 words. Always end on a complete sentence.",
            "stakes":         "400-500 words. Always end on a complete sentence.",
            "flashback":      "400-500 words. Always end on a complete sentence.",
            "chapter_end":    "350-450 words. Always end on a complete sentence.",
            "overcome_block": "3 bullets then 350-450 words. Always end on a complete sentence.",
            "fix_pacing":     "400-500 words. Always end on a complete sentence.",
            "add_tension":    "400-500 words. Always end on a complete sentence.",
            "add_specifics":  "400-500 words. Always end on a complete sentence.",
            "deepen_emotion": "400-500 words. Always end on a complete sentence.",
            "vary_style":     "400-500 words. Always end on a complete sentence.",
        }.get(action_type, "400-500 words. Always end on a complete sentence.")

        return f"""You are a master fiction writer — skilled, literary, and precise.
Your prose is of publishable quality. You write like a seasoned novelist.
You write ONLY story prose. Never explain, never break character, never refuse.
If the user's direction includes quoted dialogue, incorporate it naturally into the narrative.

STORY SETTINGS:
GENRE:  {genre}
GENRE STYLE:  {genre_cfg['style_hints']}

TONE:  {tone}
TONE INSTRUCTION:  {tone_hint}

POINT OF VIEW:  {pov}
POV INSTRUCTION:  {pov_instruction}

SCENE MOOD:  {mood}
MOOD INSTRUCTION:  {mood_instruction}{title_context}{world_section}{char_context}

ACTION:
{action_instruction}

TARGET LENGTH: {word_target}

CRAFT PRINCIPLES:
- Show, don't tell. Always.
- Every sentence must earn its place.
- Vary sentence length for rhythm and impact.
- Use specific, concrete details — never vague generalities.
- Begin with a hook, end with momentum.
- Avoid clichés. Find the fresh image, the unexpected word.
- No preamble. No meta-commentary. JUST the story.
- Do NOT say "Certainly!" or acknowledge instructions. Begin writing immediately.
"""

    def build_user_message(
        self,
        instruction: str,
        action_type: str,
        existing_story: str,
    ) -> str:
        
        story_excerpt = ""
        if existing_story:
            # Include last ~800 chars of story for context
            excerpt = existing_story[-400:] if len(existing_story) > 400 else existing_story
            story_excerpt = f"""
STORY SO FAR:
{excerpt}
---
"""
        
        if action_type in ("enhance", "rewrite") and not instruction.strip().startswith("Action:"):
            directive = f"ENHANCE/REWRITE THE ABOVE PASSAGE. Direction from author: {instruction}"
        elif action_type in ("twist", "dialogue", "describe") and instruction.startswith("Action:"):
            directive = f"Execute: {ACTION_INSTRUCTIONS[action_type]}"
        else:
            directive = instruction if instruction else "Continue the story with the same voice and momentum."
        
        return f"{story_excerpt}\n{directive}"

    def get_genre_prompts(self, genre: str) -> List[str]:
        cfg = GENRE_CONFIG.get(genre, GENRE_CONFIG["Fantasy"])
        return cfg["prompts"]

    def extract_title_suggestion(self, text: str, model: str = "llama3", ollama_url: str = "http://localhost:11434") -> str:
        """Ask Ollama to generate a compelling story title from the opening passage."""
        import requests as _req
        prompt = f"""Read this story opening and suggest ONE short, compelling title for it.
The title should be evocative, literary, and 2-5 words long.
Reply with ONLY the title — no quotes, no explanation, no punctuation at the end.

STORY OPENING:
{text[:300]}"""
        try:
            resp = _req.post(f"{ollama_url}/api/chat", json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 20}
            }, timeout=15)
            if resp.status_code == 200:
                raw = resp.json().get("message", {}).get("content", "").strip()
                # Clean up — strip quotes, punctuation, newlines
                raw = raw.strip('"\'').split('\n')[0].strip().rstrip('.,;:')
                if raw and 2 <= len(raw.split()) <= 7:
                    return raw
        except Exception:
            pass
        # Fallback: extract key phrase from first sentence
        first_sent = text.split('.')[0][:60].strip()
        words = first_sent.split()
        if len(words) >= 4:
            return " ".join(words[1:4]).title()
        return ""

    def compile_story(self, blocks: List[Dict]) -> str:
        """Compile all story blocks into clean text."""
        parts = []
        for block in blocks:
            if block["type"] == "story":
                parts.append(block["content"])
        return "\n\n".join(parts)

    def compile_story_markdown(self, blocks: List[Dict], title: str) -> str:
        """Compile story as markdown with metadata."""
        title_str = title or "Untitled Story"
        header = f"# {title_str}\n\n*Created with NARRATIVE FLOW*\n\n---\n\n"
        
        parts = [header]
        for block in blocks:
            if block["type"] == "story":
                parts.append(block["content"])
                parts.append("\n\n")
        
        return "".join(parts)

    def get_all_genres(self) -> Dict:
        return GENRE_CONFIG

    def get_all_tones(self) -> List[str]:
        return list(TONE_CONFIG.keys())