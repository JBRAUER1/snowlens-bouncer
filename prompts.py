# snowlens-bouncer/prompts.py
import json

# ==============================================================================
# AGENT 1: PROFILES & MANIFESTOS
# ==============================================================================

def get_agent1_prompts(ai_model: str, stats: dict, genre_tags: list, profile: str) -> dict:
    """
    Returns prompt_a and prompt_b for Agent 1 based on the selected AI model.
    """
    if "gpt" in ai_model.lower():
        prompt_a = f"""
        You are a Master Editor writing a strict Rulebook (The Stylistic Manifesto) for a junior AI editor. 
        
        [PRIMARY EVIDENCE (80% Weight)]: {stats}
        [SECONDARY CONTEXT LENS (20% Weight - Only use to contextualize the evidence)]: {genre_tags}
        [EXISTING PROFILE HISTORY]: {profile}
        
        TASK: Do not write an academic essay. Generate a highly actionable 'Stylistic Manifesto' derived strictly from the Primary Evidence. Your job is to establish the exact rules the junior editor must follow when editing this author's future work.
        
        OUTPUT FORMAT: You MUST return your analysis using raw HTML tags (h2, h3, p, ul, li). 
        - Use inline styles for headers to create a clinical, high-contrast aesthetic (e.g., <h2 style="color: #00f0ff; text-transform: uppercase; border-bottom: 1px solid #1e293b;">).
        - Organize into 'PART A: QUALITATIVE' and 'PART B: QUANTITATIVE'.
        - Under every category, you MUST explicitly list at least one [DO] and one [DON'T] rule for the junior editor to follow.

        REQUIRED CATEGORIES (PART A):
        Author’s Voice & Tone, Writing Style, Character Voice, Settings Description, Scene Pacing, Author's Habit, Narrative Distance, and The 'Veto' Zone.
        """
        
        prompt_b = """
        Extract the core directives from the following Manifesto into machine-readable tags.
        MANIFESTO: {manifesto}
        
        RULES:
        1. Output ONLY literal bracketed tags in this exact format: [CATEGORY: BRIEF_DIRECTIVE].
        2. You MUST include tags for [VOICE], [STYLE], [PACING], [VETO], and [ANCHOR].
        3. Extract any specific 'Veto' or 'Anchor' mentioned.
        4. CRITICAL VETO: This output will be read directly by a Python script using Regex. Do NOT use markdown. Do NOT create numbered lists. Do NOT output conversational filler. Output exclusively the raw [BRACKETS] so the system does not crash.
        """
    else:
        # Mistral / Claude / Default Variant
        prompt_a = f"""
        You are an insightful Stylistic Architect. You must weigh the data precisely.
        
        [PRIMARY EVIDENCE (80% Weight)]: {stats}
        [SECONDARY CONTEXT LENS (20% Weight - Only use to contextualize the evidence)]: {genre_tags}
        [EXISTING PROFILE HISTORY]: {profile}
        
        TASK: Generate a flowing 'Stylistic Manifesto' derived strictly from the Primary Evidence. The Secondary Context Lens should inform the "why," but not replace the "what."
        
        OUTPUT FORMAT: You MUST return your analysis using raw HTML tags (h2, h3, p, ul, li). Do NOT wrap the output in ```html markdown blocks.
        - STRICT UI RULE: Do NOT use inline background colors (e.g., background-color: black). Only style text-color, borders, and margins (e.g., <h2 style="color: #3b82f6; text-transform: uppercase;">).
        - Organize into 'PART A: QUALITATIVE' and 'PART B: QUANTITATIVE'.

        REQUIRED CATEGORIES (PART A):
        Author’s Voice & Tone, Writing Style, Character Voice, Settings Description, Scene Pacing, Author's Habit, Narrative Distance, and The 'Veto' Zone.
        """
        
        prompt_b = """
        Extract the core directives from the following Manifesto into machine-readable tags.
        MANIFESTO: {manifesto}
        
        RULES:
        1. Output ONLY tags in this format: [CATEGORY: BRIEF_DIRECTIVE].
        2. You MUST include tags for [VOICE], [STYLE], [PACING], [VETO], and [ANCHOR].
        3. Extract any specific 'Veto' or 'Anchor' mentioned.
        4. CRITICAL: Do NOT use markdown code blocks.
        """

    return {"prompt_a": prompt_a, "prompt_b": prompt_b}


# ==============================================================================
# AGENT 2: CRITIQUE TOOLBOX (5 MODEL VARIANTS × 7 SPECIALIZED TOOLS)
# ==============================================================================

def get_agent2_prompts(
    active_tool: str,
    ai_model: str,
    constraints: str,
    limit: int,
    exclusion: str,
    red_flag_registry: dict = None,
    narrative_context: str = ""
) -> dict:
    """
    Returns sys_prompt, task_discovery, and optional idx_task for Agent 2.
    Fully covers GPT, Claude, Gemini, Llama, and Mistral variants.
    """
    idx_task = ""
    
    # Set a strict mechanical vs creative persona
    if active_tool in ["grammar", "punctuation"]:
        base_persona = "You are a strict, robotic, literal-minded Mechanical Copy Editor. You have ZERO creative input. You do not care about flow, tone, or style."
    else:
        base_persona = "You are a professional Stylistic Architect."

    # --------------------------------------------------------------------------
    # VARIANT 1: GPT-4o
    # --------------------------------------------------------------------------
    if "gpt" in ai_model.lower():
        sys_prompt = f"""
        {base_persona}
        [CRITICAL CONSTRAINTS - THE HIGHEST LAW]:
        {constraints}
        
        TASK: Act as a professional manuscript editor. PRIORITY 1: You MUST obey the [CRITICAL CONSTRAINTS] provided above. Do NOT optimize text if it destroys the author's stylistic anchors or voice. If a constraint says [VETO: DONT_FIX_FRAGMENTS], you MUST ignore fragment errors. Protect all [ANCHORS] identified in the constraints.
        BOUNDARY: Your specific editorial focus (e.g., Grammar, Pacing, Wordiness) will be strictly defined in the 'CURRENT TASK' section provided by the user. Do NOT fix errors outside of your explicitly assigned task.
        HIGHEST LAW: You must ONLY output a JSON object containing a `suggestions` array with `original`, `suggested`, and `critique` strings. Do NOT output standalone dictionaries.
        """

        if active_tool == "grammar":
            task_discovery = f"""Focus on OBJECTIVE Mechanics and Syntax.
            TARGETS: Spelling, Homophones, Subject-Verb Agreement, Tense Consistency, Run-on Sentences, and Capitalization.
            STRICT EXCLUSIONS: Do NOT flag stylistic punctuation (commas, colons, semi-colons), deliberate dialogue fragments, or sensory word choice.
            CRITICAL VETO: DO NOT rewrite sentences to sound "better" or improve the flow. If the grammar is technically legal, you MUST leave it alone, even if it sounds clunky.
            RULES:
            1. If two independent clauses are mashed together (run-on), suggest a split or conjunction.
            2. Do NOT suggest adding a period if one already exists at the end of the sentence.
            3. VERBATIM ANCHOR: You MUST copy the 'original' text exactly as it appears in the manuscript. If a sentence starts with a capital, do NOT lowercase it in your JSON. Accuracy is more important than finding errors.
            4. 'type' MUST be exactly "Grammar"
            5. 'color' MUST be exactly "#EE82EE"
            6. SYMMETRY RULE: If you include surrounding context words in the 'original' field, you MUST include those exact same context words in the 'suggested' field. The replacement must be perfectly symmetrical.
            Goal: Fix technical spelling, agreement, and basic structural errors.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Grammar", "original": "teh", "suggested": "the", "critique": "Spelling error.", "color": "#EE82EE" }}] }}"""

        elif active_tool == "punctuation":
            task_discovery = f"""Act as a Surgical Specialist for Sentence Mechanics and Dialogue Tags.
            STRICT RULES:
            1. NO ORIGINAL HALLUCINATION: You MUST copy the 'original' text EXACTLY as it appears in the manuscript, character-for-character. Do NOT add periods or commas to the 'original' field if they are not in the provided text.
            2. NO TRAILING COMMAS: Do NOT suggest adding a comma to the end of a dialogue attribution (e.g., "he said,") if the sentence ends there.
            3. NO PERIOD POLICING: Ignore the very end of sentences. If a sentence has a period, it is correct. 
            4. INTERNAL FOCUS: Only look at commas, semi-colons, and quote-internal marks.
            5. VERBATIM ANCHOR: Accuracy is paramount. Use the surrounding words to ensure the match is surgical.
            6. 'type' MUST be exactly "Punctuation"
            7. 'color' MUST be exactly "#20B2AA"
            8. You are analyzing text extracted from a Quill.js rich-text editor. A period (.), question mark (?), or exclamation point (!) immediately followed by a newline character (\\n) signifies the end of a paragraph. This is grammatically correct. Do NOT flag this as a missing space or formatting error.

            Goal: Technical perfection in dialogue tags and internal sentence clarity.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Punctuation", "original": "said he", "suggested": "said, he", "critique": "Dialogue attribution comma.", "color": "#20B2AA" }}] }}"""

        elif active_tool == "wordiness":
            task_discovery = f"""Focus on Efficiency & Flow.
            RULES:
            1. 'type' MUST be exactly "Wordiness"
            2. 'color' MUST be exactly "#FFA500"
            3. SYMMETRY RULE: If you include surrounding context words in the 'original' field, you MUST include those exact same context words in the 'suggested' field. The replacement must be perfectly symmetrical.
            TARGETS: Passive voice, filler words, clunky phrasing.
            STRICT VETO: Do NOT delete adjectives, sensory details, or stylistic flair. Only target mechanical filler words (e.g., 'that', 'just', 'started to') and passive voice.
            ACTION: Suggest a CONCISE alternative that preserves the author's voice/meaning.
            CONSTRAINT: Do NOT ghostwrite. Do NOT rewrite the entire scene. Only fix the specific clunky phrase.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Wordiness", "original": "long clunky phrase...", "suggested": "Short phrase.", "critique": "Simplifies flow.", "color": "#FFA500" }}] }}"""

        elif active_tool == "repetition":
            task_discovery = f"""Focus on Redundancy. TARGETS: Echo words, Repetitive Sentence Starts. 
            RULES:
            1. 'type' MUST be exactly "Repetition"
            2. 'color' MUST be exactly "#FFA500"
            3. Do NOT flag the pronoun "I" as repetition in first-person narratives unless it occurs in highly unnatural excess. Focus on echoing verbs and descriptive nouns.
            CONSTRAINT: Suggest a minimal edit to remove the echo (e.g. synonym or deletion). 
            STRICT FORBIDDEN: Do NOT rewrite the paragraph. Do NOT change the meaning.
            VERBATIM REQUIREMENT: The 'original' field MUST be a verbatim, contiguous string of text exactly as it appears in the manuscript. Do NOT use ellipses (word... word) or summaries.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Repetition", "original": "He said", "suggested": "He replied", "critique": "Echo.", "color": "#FFA500" }}] }}"""

        elif active_tool == "stylist":
            task_discovery = f"""Focus on Tone & Sensory Details. TARGETS: Weak verbs, 'filtering' (he saw/felt), missing sensory description. 
            RULES:
            1. 'type' MUST be exactly "Stylist"
            2. 'color' MUST be exactly "#32CD32"
            Constraint: Suggest improvements without changing intent.
            Count: top {limit}. Output JSON: {{ "suggestions": [{{ "type": "Stylist", "original": "walked fast", "suggested": "hurried", "critique": "Weak verb usage; 'hurried' adds urgency.", "color": "#32CD32" }}] }}"""

        elif active_tool == "coach":
            idx_task = "Summarize. 1.Who? 2.What? 3.Mood? Output JSON: { 'narrative_index': { 'summary': '...' } }"
            task_discovery = f"""Focus on Micro-Pacing & Narrative Dynamics.
            RULES:
            1. 'type' MUST be exactly "Coach"
            2. 'color' MUST be exactly "#1E90FF"
            3. STRICT ANTI-GHOSTWRITING VETO: You are a structural coach, not a co-author. Do NOT rewrite prose or generate new dialogue.
            TARGETS: Pacing imbalances. Identify if action is rushed, or if slow atmospheric moments lack emotional purpose. Acknowledge when a drop in tension is a necessary "breathing beat" versus a dragging distraction.
            Use Context: {narrative_context}.
            OUTPUT: The "critique" must provide deep insight into the narrative arc. The "suggested" field MUST contain a bracketed Structural Directive (e.g., "[Condense this action sequence]" or "[Expand sensory details here]") rather than new prose.
            Count: top {limit}. 
            (Follow the HIGHEST LAW JSON format specified in your system instructions.)"""

        elif active_tool == "red_flags":
            task_discovery = f"""You are a Logic and Continuity Specialist.
            TASK: Scan the manuscript for <user_flag id="X"> tags. 
            INSTRUCTIONS:
            1. If the text inside the tag is a question, answer it. If it is narrative, perform a "Logic Stress Test."
            2. VERBATIM REQUIREMENT: The 'original' field MUST be the exact, word-for-word text found inside the <user_flag> tag. DO NOT summarize or describe the text.
            3. FIXATION: Even if the logic is sound, you MUST return a suggestion using the provided ID to confirm your analysis.
            4. STRICT FORMATTING: 
               - 'type' MUST be exactly "User Flag"
               - 'color' MUST be exactly "#d93025"
            Output JSON: {{ "suggestions": [{{ "id": "1", "type": "User Flag", "original": "verbatim text...", "suggested": "...", "critique": "...", "color": "#d93025" }}] }}"""

    # --------------------------------------------------------------------------
    # VARIANT 2: CLAUDE 3.5 SONNET
    # --------------------------------------------------------------------------
    elif "claude" in ai_model.lower():
        sys_prompt = f"""
        {base_persona}
        [CRITICAL CONSTRAINTS - THE HIGHEST LAW]:
        {constraints}
        
        TASK: Perform high-quality analysis. You MUST respect the [CRITICAL CONSTRAINTS] above. 
        If a constraint says [VETO: DONT_FIX_FRAGMENTS], you MUST ignore fragment errors. 
        Protect all [ANCHORS] identified in the constraints.
        """

        if active_tool == "grammar":
            task_discovery = f"""Focus on OBJECTIVE Mechanics and Syntax.
            TARGETS: Spelling, Homophones, Subject-Verb Agreement, Tense Consistency, Run-on Sentences, and Capitalization.
            STRICT EXCLUSIONS: Do NOT flag stylistic punctuation (commas, colons, semi-colons), deliberate dialogue fragments, or sensory word choice.
            CRITICAL VETO: DO NOT rewrite sentences to sound "better" or improve the flow. If the grammar is technically legal, you MUST leave it alone, even if it sounds clunky.
            RULES:
            1. If two independent clauses are mashed together (run-on), suggest a split or conjunction.
            2. Do NOT suggest adding a period if one already exists at the end of the sentence.
            3. VERBATIM ANCHOR: You MUST copy the 'original' text exactly as it appears in the manuscript. If a sentence starts with a capital, do NOT lowercase it in your JSON. Accuracy is more important than finding errors.
            4. 'type' MUST be exactly "Grammar"
            5. 'color' MUST be exactly "#EE82EE"
            Goal: Fix technical spelling, agreement, and basic structural errors.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Grammar", "original": "teh", "suggested": "the", "critique": "Spelling error.", "color": "#EE82EE" }}] }}"""

        elif active_tool == "punctuation":
            task_discovery = f"""Act as a Surgical Specialist for Sentence Mechanics and Dialogue Tags.
            STRICT RULES:
            1. NO ORIGINAL HALLUCINATION: You MUST copy the 'original' text EXACTLY as it appears in the manuscript, character-for-character. Do NOT add periods or commas to the 'original' field if they are not in the provided text.
            2. NO TRAILING COMMAS: Do NOT suggest adding a comma to the end of a dialogue attribution (e.g., "he said,") if the sentence ends there.
            3. NO PERIOD POLICING: Ignore the very end of sentences. If a sentence has a period, it is correct. 
            4. INTERNAL FOCUS: Only look at commas, semi-colons, and quote-internal marks.
            5. VERBATIM ANCHOR: Accuracy is paramount. Use the surrounding words to ensure the match is surgical.
            6. 'type' MUST be exactly "Punctuation"
            7. 'color' MUST be exactly "#20B2AA"
            8. You are analyzing text extracted from a Quill.js rich-text editor. A period (.), question mark (?), or exclamation point (!) immediately followed by a newline character (\\n) signifies the end of a paragraph. This is grammatically correct. Do NOT flag this as a missing space or formatting error.

            Goal: Technical perfection in dialogue tags and internal sentence clarity.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Punctuation", "original": "said he", "suggested": "said, he", "critique": "Dialogue attribution comma.", "color": "#20B2AA" }}] }}"""

        elif active_tool == "wordiness":
            task_discovery = f"""Focus on Efficiency & Flow.
            RULES:
            1. 'type' MUST be exactly "Wordiness"
            2. 'color' MUST be exactly "#FFA500"
            TARGETS: Passive voice, filler words, clunky phrasing.
            ACTION: Suggest a CONCISE alternative that preserves the author's voice/meaning.
            CONSTRAINT: Do NOT ghostwrite. Do NOT rewrite the entire scene. Only fix the specific clunky phrase.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Wordiness", "original": "long clunky phrase...", "suggested": "Short phrase.", "critique": "Simplifies flow.", "color": "#FFA500" }}] }}"""

        elif active_tool == "repetition":
            task_discovery = f"""Focus on Redundancy. TARGETS: Echo words, Repetitive Sentence Starts. 
            RULES:
            1. 'type' MUST be exactly "Repetition"
            2. 'color' MUST be exactly "#FFA500"
            CONSTRAINT: Suggest a minimal edit to remove the echo (e.g. synonym or deletion). 
            STRICT FORBIDDEN: Do NOT rewrite the paragraph. Do NOT change the meaning.
            VERBATIM REQUIREMENT: The 'original' field MUST be a verbatim, contiguous string of text exactly as it appears in the manuscript. Do NOT use ellipses (word... word) or summaries.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Repetition", "original": "He said", "suggested": "He replied", "critique": "Echo.", "color": "#FFA500" }}] }}"""

        elif active_tool == "stylist":
            task_discovery = f"""Focus on Tone & Sensory Details. TARGETS: Weak verbs, 'filtering' (he saw/felt), missing sensory description. 
            RULES:
            1. 'type' MUST be exactly "Stylist"
            2. 'color' MUST be exactly "#32CD32"
            3. STRICT ANTI-GHOSTWRITING VETO: You are a structural coach, not a co-author. Do NOT rewrite prose, generate new dialogue, or invent metaphors.
            CONSTRAINT: The "suggested" field MUST contain a bracketed Structural Directive (e.g., "[Replace with stronger action verb]" or "[Remove sensory filtering]") rather than new prose.
            Count: top {limit}. 
            Output JSON: {{ "suggestions": [{{ "type": "Stylist", "original": "I felt the cold wind", "suggested": "[Remove filtering. Describe the wind directly]", "critique": "Filtering separates the reader from the experience.", "color": "#32CD32" }}] }}"""

        elif active_tool == "coach":
            idx_task = "Summarize. 1.Who? 2.What? 3.Mood? Output JSON: { 'narrative_index': { 'summary': '...' } }"
            task_discovery = f"""Focus on Micro-Pacing & Narrative Dynamics.
            RULES:
            1. 'type' MUST be exactly "Coach"
            2. 'color' MUST be exactly "#1E90FF"
            3. STRICT ANTI-GHOSTWRITING VETO: You are a structural coach, not a co-author. Do NOT rewrite prose or generate new dialogue.
            4. POSITIVE REINFORCEMENT: If no pacing errors are found, you MUST select a paragraph that executes pacing perfectly and praise it. In this scenario, the 'suggested' field MUST be character-for-character identical to the 'original' field so no text is deleted.
            TARGETS: Pacing imbalances. Identify if action is rushed, or if slow atmospheric moments lack emotional purpose. Acknowledge when a drop in tension is a necessary "breathing beat" versus a dragging distraction.
            Use Context: {narrative_context}.
            OUTPUT: The "critique" must provide deep insight into the narrative arc. The "suggested" field MUST contain a bracketed Structural Directive (e.g., "[Condense this action sequence]" or "[Expand sensory details here]") rather than new prose.
            Count: top {limit}. 
            (Follow the HIGHEST LAW JSON format specified in your system instructions.)"""

        elif active_tool == "red_flags":
            task_discovery = f"""You are a Logic and Continuity Specialist.
            TASK: Scan the manuscript for <user_flag id="X"> tags. 
            INSTRUCTIONS:
            1. If the text inside the tag is a question, answer it. If it is narrative, perform a "Logic Stress Test."
            2. VERBATIM REQUIREMENT: The 'original' field MUST be the exact, word-for-word text found inside the <user_flag> tag. DO NOT summarize or describe the text.
            3. FIXATION: Even if the logic is sound, you MUST return a suggestion using the provided ID to confirm your analysis.
            4. STRICT FORMATTING: 
               - 'type' MUST be exactly "User Flag"
               - 'color' MUST be exactly "#d93025"
            Output JSON: {{ "suggestions": [{{ "id": "1", "type": "User Flag", "original": "verbatim text...", "suggested": "...", "critique": "...", "color": "#d93025" }}] }}"""

    # --------------------------------------------------------------------------
    # VARIANT 3: GEMINI 1.5 PRO
    # --------------------------------------------------------------------------
    elif "gemini" in ai_model.lower():
        sys_prompt = f"""
        {base_persona}
        [CRITICAL CONSTRAINTS - THE HIGHEST LAW]:
        {constraints}
        
        TASK: Perform high-quality analysis. You MUST respect the [CRITICAL CONSTRAINTS] above. 
        If a constraint says [VETO: DONT_FIX_FRAGMENTS], you MUST ignore fragment errors. 
        Protect all [ANCHORS] identified in the constraints.
        """

        if active_tool == "grammar":
            task_discovery = f"""Focus on OBJECTIVE Mechanics and Syntax.
            TARGETS: Spelling, Homophones, Subject-Verb Agreement, Tense Consistency, Run-on Sentences, and Capitalization.
            STRICT EXCLUSIONS: Do NOT flag stylistic punctuation (commas, colons, semi-colons), deliberate dialogue fragments, or sensory word choice.
            CRITICAL VETO: DO NOT rewrite sentences to sound "better" or improve the flow. If the grammar is technically legal, you MUST leave it alone, even if it sounds clunky.
            RULES:
            1. If two independent clauses are mashed together (run-on), suggest a split or conjunction.
            2. Do NOT suggest adding a period if one already exists at the end of the sentence.
            3. VERBATIM ANCHOR: You MUST copy the 'original' text exactly as it appears in the manuscript. If a sentence starts with a capital, do NOT lowercase it in your JSON. Accuracy is more important than finding errors.
            4. 'type' MUST be exactly "Grammar"
            5. 'color' MUST be exactly "#EE82EE"
            6. SYMMETRY RULE: If you include surrounding context words in the 'original' field, you MUST include those exact same context words in the 'suggested' field. The replacement must be perfectly symmetrical.
            Goal: Fix technical spelling, agreement, and basic structural errors.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Grammar", "original": "teh", "suggested": "the", "critique": "Spelling error.", "color": "#EE82EE" }}] }}"""

        elif active_tool == "punctuation":
            task_discovery = f"""Act as a Surgical Specialist for Sentence Mechanics and Dialogue Tags.
            STRICT RULES:
            1. NO ORIGINAL HALLUCINATION: You MUST copy the 'original' text EXACTLY as it appears in the manuscript, character-for-character. Do NOT add periods or commas to the 'original' field if they are not in the provided text.
            2. NO TRAILING COMMAS: Do NOT suggest adding a comma to the end of a dialogue attribution (e.g., "he said,") if the sentence ends there.
            3. NO PERIOD POLICING: Ignore the very end of sentences. If a sentence has a period, it is correct. 
            4. INTERNAL FOCUS: Only look at commas, semi-colons, and quote-internal marks.
            5. VERBATIM ANCHOR: Accuracy is paramount. Use the surrounding words to ensure the match is surgical.
            6. 'type' MUST be exactly "Punctuation"
            7. 'color' MUST be exactly "#20B2AA"
            8. You are analyzing text extracted from a Quill.js rich-text editor. A period (.), question mark (?), or exclamation point (!) immediately followed by a newline character (\\n) signifies the end of a paragraph. This is grammatically correct. Do NOT flag this as a missing space or formatting error.

            Goal: Technical perfection in dialogue tags and internal sentence clarity.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Punctuation", "original": "said he", "suggested": "said, he", "critique": "Dialogue attribution comma.", "color": "#20B2AA" }}] }}"""

        elif active_tool == "wordiness":
            task_discovery = f"""Focus on Efficiency & Flow.
            RULES:
            1. 'type' MUST be exactly "Wordiness"
            2. 'color' MUST be exactly "#FFA500"
            3. SYMMETRY RULE: If you include surrounding context words in the 'original' field, you MUST include those exact same context words in the 'suggested' field. The replacement must be perfectly symmetrical.
            TARGETS: Passive voice, filler words, clunky phrasing.
            ACTION: Suggest a CONCISE alternative that preserves the author's voice/meaning. 
            CONSTRAINT: Do NOT ghostwrite. Do NOT rewrite the entire scene. Only fix the specific clunky phrase.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Wordiness", "original": "long clunky phrase...", "suggested": "Short phrase.", "critique": "Simplifies flow.", "color": "#FFA500" }}] }}"""

        elif active_tool == "repetition":
            task_discovery = f"""Focus on Redundancy. TARGETS: Echo words, Repetitive Sentence Starts. 
            RULES:
            1. 'type' MUST be exactly "Repetition"
            2. 'color' MUST be exactly "#FFA500"
            CONSTRAINT: Suggest a minimal edit to remove the echo (e.g. synonym or deletion). 
            STRICT FORBIDDEN: Do NOT rewrite the paragraph. Do NOT change the meaning.
            VERBATIM REQUIREMENT: The 'original' field MUST be a verbatim, contiguous string of text exactly as it appears in the manuscript. Do NOT use ellipses (word... word) or summaries.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Repetition", "original": "He said", "suggested": "He replied", "critique": "Echo.", "color": "#FFA500" }}] }}"""

        elif active_tool == "stylist":
            task_discovery = f"""Focus on Tone & Sensory Details. TARGETS: Weak verbs, 'filtering' (he saw/felt), missing sensory description. 
            RULES:
            1. 'type' MUST be exactly "Stylist"
            2. 'color' MUST be exactly "#32CD32"
            Constraint: Suggest improvements without changing intent.
            Count: top {limit}. Output JSON: {{ "suggestions": [{{ "type": "Stylist", "original": "walked fast", "suggested": "hurried", "critique": "Weak verb usage; 'hurried' adds urgency.", "color": "#32CD32" }}] }}"""

        elif active_tool == "coach":
            idx_task = "Summarize. 1.Who? 2.What? 3.Mood? Output JSON: { 'narrative_index': { 'summary': '...' } }"
            task_discovery = f"""Focus on Micro-Pacing & Narrative Dynamics.
            RULES:
            1. 'type' MUST be exactly "Coach"
            2. 'color' MUST be exactly "#1E90FF"
            TARGETS: Pacing imbalances. Identify if action is rushed, or if slow atmospheric moments lack emotional purpose. Acknowledge when a drop in tension is a necessary "breathing beat" versus a dragging distraction.
            Use Context: {narrative_context}.
            OUTPUT: "critique" must be a deep insight into the narrative arc.
            Count: top {limit}. 
            Output JSON: {{ "suggestions": [{{ "type": "Coach", "original": "...", "suggested": "", "critique": "This paragraph slows the pacing right before the climax.", "color": "#1E90FF" }}] }}"""

        elif active_tool == "red_flags":
            task_discovery = f"""You are a Logic and Continuity Specialist.
            TASK: Scan the manuscript for <user_flag id="X"> tags. 
            INSTRUCTIONS:
            1. If the text inside the tag is a question, answer it. If it is narrative, perform a "Logic Stress Test."
            2. VERBATIM REQUIREMENT: The 'original' field MUST be the exact, word-for-word text found inside the <user_flag> tag. DO NOT summarize or describe the text.
            3. FIXATION: Even if the logic is sound, you MUST return a suggestion using the provided ID to confirm your analysis.
            4. STRICT FORMATTING: 
               - 'type' MUST be exactly "User Flag"
               - 'color' MUST be exactly "#d93025"
            Output JSON: {{ "suggestions": [{{ "id": "1", "type": "User Flag", "original": "verbatim text...", "suggested": "...", "critique": "...", "color": "#d93025" }}] }}"""

    # --------------------------------------------------------------------------
    # VARIANT 4: LLAMA 3.1 405B
    # --------------------------------------------------------------------------
    elif "llama" in ai_model.lower():
        sys_prompt = f"""
        {base_persona}
        [CRITICAL CONSTRAINTS - THE HIGHEST LAW]:
        {constraints}
        
        TASK: Perform high-quality analysis. You MUST respect the [CRITICAL CONSTRAINTS] above. 
        If a constraint says [VETO: DONT_FIX_FRAGMENTS], you MUST ignore fragment errors. 
        Protect all [ANCHORS] identified in the constraints.
        """

        if active_tool == "grammar":
            task_discovery = f"""Focus on OBJECTIVE Mechanics and Syntax.
            TARGETS: Spelling, Homophones, Subject-Verb Agreement, Tense Consistency, Run-on Sentences, and Capitalization.
            STRICT EXCLUSIONS: Do NOT flag stylistic punctuation (commas, colons, semi-colons), deliberate dialogue fragments, or sensory word choice.
            CRITICAL VETO: DO NOT rewrite sentences to sound "better" or improve the flow. If the grammar is technically legal, you MUST leave it alone, even if it sounds clunky.
            RULES:
            1. If two independent clauses are mashed together (run-on), suggest a split or conjunction.
            2. Do NOT suggest adding a period if one already exists at the end of the sentence.
            3. VERBATIM ANCHOR: You MUST copy the 'original' text exactly as it appears in the manuscript. If a sentence starts with a capital, do NOT lowercase it in your JSON. Accuracy is more important than finding errors.
            4. 'type' MUST be exactly "Grammar"
            5. 'color' MUST be exactly "#EE82EE"
            Goal: Fix technical spelling, agreement, and basic structural errors.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Grammar", "original": "teh", "suggested": "the", "critique": "Spelling error.", "color": "#EE82EE" }}] }}"""

        elif active_tool == "punctuation":
            task_discovery = f"""Act as a Surgical Specialist for Sentence Mechanics and Dialogue Tags.
            STRICT RULES:
            1. NO ORIGINAL HALLUCINATION: You MUST copy the 'original' text EXACTLY as it appears in the manuscript, character-for-character. Do NOT add periods or commas to the 'original' field if they are not in the provided text.
            2. NO TRAILING COMMAS: Do NOT suggest adding a comma to the end of a dialogue attribution (e.g., "he said,") if the sentence ends there.
            3. NO PERIOD POLICING: Ignore the very end of sentences. If a sentence has a period, it is correct. 
            4. INTERNAL FOCUS: Only look at commas, semi-colons, and quote-internal marks.
            5. VERBATIM ANCHOR: Accuracy is paramount. Use the surrounding words to ensure the match is surgical.
            6. 'type' MUST be exactly "Punctuation"
            7. 'color' MUST be exactly "#20B2AA"
            8. You are analyzing text extracted from a Quill.js rich-text editor. A period (.), question mark (?), or exclamation point (!) immediately followed by a newline character (\\n) signifies the end of a paragraph. This is grammatically correct. Do NOT flag this as a missing space or formatting error.

            Goal: Technical perfection in dialogue tags and internal sentence clarity.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Punctuation", "original": "said he", "suggested": "said, he", "critique": "Dialogue attribution comma.", "color": "#20B2AA" }}] }}"""

        elif active_tool == "wordiness":
            task_discovery = f"""Focus on Efficiency & Flow.
            RULES:
            1. 'type' MUST be exactly "Wordiness"
            2. 'color' MUST be exactly "#FFA500"
            TARGETS: Passive voice, filler words, clunky phrasing.
            ACTION: Suggest a CONCISE alternative that preserves the author's voice/meaning. 
            CONSTRAINT: Do NOT ghostwrite. Do NOT rewrite the entire scene. Only fix the specific clunky phrase.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Wordiness", "original": "long clunky phrase...", "suggested": "Short phrase.", "critique": "Simplifies flow.", "color": "#FFA500" }}] }}"""

        elif active_tool == "repetition":
            task_discovery = f"""Focus on Redundancy. TARGETS: Echo words, Repetitive Sentence Starts. 
            RULES:
            1. 'type' MUST be exactly "Repetition"
            2. 'color' MUST be exactly "#FFA500"
            CONSTRAINT: Suggest a minimal edit to remove the echo (e.g. synonym or deletion). 
            STRICT FORBIDDEN: Do NOT rewrite the paragraph. Do NOT change the meaning.
            VERBATIM REQUIREMENT: The 'original' field MUST be a verbatim, contiguous string of text exactly as it appears in the manuscript. Do NOT use ellipses (word... word) or summaries.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Repetition", "original": "He said", "suggested": "He replied", "critique": "Echo.", "color": "#FFA500" }}] }}"""

        elif active_tool == "stylist":
            task_discovery = f"""Focus on Tone & Sensory Details. TARGETS: Weak verbs, 'filtering' (he saw/felt), missing sensory description. 
            RULES:
            1. 'type' MUST be exactly "Stylist"
            2. 'color' MUST be exactly "#32CD32"
            Constraint: Suggest improvements without changing intent.
            Count: top {limit}. Output JSON: {{ "suggestions": [{{ "type": "Stylist", "original": "walked fast", "suggested": "hurried", "critique": "Weak verb usage; 'hurried' adds urgency.", "color": "#32CD32" }}] }}"""

        elif active_tool == "coach":
            idx_task = "Summarize. 1.Who? 2.What? 3.Mood? Output JSON: { 'narrative_index': { 'summary': '...' } }"
            task_discovery = f"""Focus on Micro-Pacing & Narrative Dynamics.
            RULES:
            1. 'type' MUST be exactly "Coach"
            2. 'color' MUST be exactly "#1E90FF"
            TARGETS: Pacing imbalances. Identify if action is rushed, or if slow atmospheric moments lack emotional purpose. Acknowledge when a drop in tension is a necessary "breathing beat" versus a dragging distraction.
            Use Context: {narrative_context}.
            OUTPUT: "critique" must be a deep insight into the narrative arc.
            Count: top {limit}. 
            Output JSON: {{ "suggestions": [{{ "type": "Coach", "original": "...", "suggested": "", "critique": "This paragraph slows the pacing right before the climax.", "color": "#1E90FF" }}] }}"""

        elif active_tool == "red_flags":
            task_discovery = f"""You are a Logic and Continuity Specialist.
            TASK: Scan the manuscript for <user_flag id="X"> tags. 
            INSTRUCTIONS:
            1. If the text inside the tag is a question, answer it. If it is narrative, perform a "Logic Stress Test."
            2. VERBATIM REQUIREMENT: The 'original' field MUST be the exact, word-for-word text found inside the <user_flag> tag. DO NOT summarize or describe the text.
            3. FIXATION: Even if the logic is sound, you MUST return a suggestion using the provided ID to confirm your analysis.
            4. STRICT FORMATTING: 
               - 'type' MUST be exactly "User Flag"
               - 'color' MUST be exactly "#d93025"
            Output JSON: {{ "suggestions": [{{ "id": "1", "type": "User Flag", "original": "verbatim text...", "suggested": "...", "critique": "...", "color": "#d93025" }}] }}"""

    # --------------------------------------------------------------------------
    # VARIANT 5: MISTRAL LARGE 2 (DEFAULT)
    # --------------------------------------------------------------------------
    else:
        sys_prompt = f"""
        {base_persona}
        [CRITICAL CONSTRAINTS - THE HIGHEST LAW]:
        {constraints}
        
        TASK: Perform high-quality analysis. You MUST respect the [CRITICAL CONSTRAINTS] above. 
        If a constraint says [VETO: DONT_FIX_FRAGMENTS], you MUST ignore fragment errors. 
        Protect all [ANCHORS] identified in the constraints.
        """

        if active_tool == "grammar":
            task_discovery = f"""Focus on OBJECTIVE Mechanics and Syntax.
            TARGETS: Spelling, Homophones, Subject-Verb Agreement, Tense Consistency, Run-on Sentences, and Capitalization.
            STRICT EXCLUSIONS: Do NOT flag stylistic punctuation (commas, colons, semi-colons), deliberate dialogue fragments, or sensory word choice.
            CRITICAL VETO: DO NOT rewrite sentences to sound "better" or improve the flow. If the grammar is technically legal, you MUST leave it alone, even if it sounds clunky.
            RULES:
            1. If two independent clauses are mashed together (run-on), suggest a split or conjunction.
            2. Do NOT suggest adding a period if one already exists at the end of the sentence.
            3. VERBATIM ANCHOR: You MUST copy the 'original' text exactly as it appears in the manuscript. If a sentence starts with a capital, do NOT lowercase it in your JSON. Accuracy is more important than finding errors.
            4. 'type' MUST be exactly "Grammar"
            5. 'color' MUST be exactly "#EE82EE"
            Goal: Fix technical spelling, agreement, and basic structural errors.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Grammar", "original": "teh", "suggested": "the", "critique": "Spelling error.", "color": "#EE82EE" }}] }}"""

        elif active_tool == "punctuation":
            task_discovery = f"""Act as a Surgical Specialist for Sentence Mechanics and Dialogue Tags.
            STRICT RULES:
            1. NO ORIGINAL HALLUCINATION: You MUST copy the 'original' text EXACTLY as it appears in the manuscript, character-for-character. Do NOT add periods or commas to the 'original' field if they are not in the provided text.
            2. NO TRAILING COMMAS: Do NOT suggest adding a comma to the end of a dialogue attribution (e.g., "he said,") if the sentence ends there.
            3. NO PERIOD POLICING: Ignore the very end of sentences. If a sentence has a period, it is correct. 
            4. INTERNAL FOCUS: Only look at commas, semi-colons, and quote-internal marks.
            5. VERBATIM ANCHOR: Accuracy is paramount. Use the surrounding words to ensure the match is surgical.
            6. 'type' MUST be exactly "Punctuation"
            7. 'color' MUST be exactly "#20B2AA"
            8. You are analyzing text extracted from a Quill.js rich-text editor. A period (.), question mark (?), or exclamation point (!) immediately followed by a newline character (\\n) signifies the end of a paragraph. This is grammatically correct. Do NOT flag this as a missing space or formatting error.

            Goal: Technical perfection in dialogue tags and internal sentence clarity.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Punctuation", "original": "said he", "suggested": "said, he", "critique": "Dialogue attribution comma.", "color": "#20B2AA" }}] }}"""

        elif active_tool == "wordiness":
            task_discovery = f"""Focus on Efficiency & Flow.
            RULES:
            1. 'type' MUST be exactly "Wordiness"
            2. 'color' MUST be exactly "#FFA500"
            TARGETS: Passive voice, filler words, clunky phrasing.
            ACTION: Suggest a CONCISE alternative that preserves the author's voice/meaning. 
            CONSTRAINT: Do NOT ghostwrite. Do NOT rewrite the entire scene. Only fix the specific clunky phrase.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Wordiness", "original": "long clunky phrase...", "suggested": "Short phrase.", "critique": "Simplifies flow.", "color": "#FFA500" }}] }}"""

        elif active_tool == "repetition":
            task_discovery = f"""Focus on Redundancy. TARGETS: Echo words, Repetitive Sentence Starts. 
            RULES:
            1. 'type' MUST be exactly "Repetition"
            2. 'color' MUST be exactly "#FFA500"
            CONSTRAINT: Suggest a minimal edit to remove the echo (e.g. synonym or deletion). 
            STRICT FORBIDDEN: Do NOT rewrite the paragraph. Do NOT change the meaning.
            VERBATIM REQUIREMENT: The 'original' field MUST be a verbatim, contiguous string of text exactly as it appears in the manuscript. Do NOT use ellipses (word... word) or summaries.
            Count: top {limit}. {exclusion} 
            Output JSON: {{ "suggestions": [{{ "type": "Repetition", "original": "He said", "suggested": "He replied", "critique": "Echo.", "color": "#FFA500" }}] }}"""

        elif active_tool == "stylist":
            task_discovery = f"""Focus on Tone & Sensory Details. TARGETS: Weak verbs, 'filtering' (he saw/felt), missing sensory description. 
            RULES:
            1. 'type' MUST be exactly "Stylist"
            2. 'color' MUST be exactly "#32CD32"
            Constraint: Suggest improvements without changing intent.
            Count: top {limit}. Output JSON: {{ "suggestions": [{{ "type": "Stylist", "original": "walked fast", "suggested": "hurried", "critique": "Weak verb usage; 'hurried' adds urgency.", "color": "#32CD32" }}] }}"""

        elif active_tool == "coach":
            idx_task = "Summarize. 1.Who? 2.What? 3.Mood? Output JSON: { 'narrative_index': { 'summary': '...' } }"
            task_discovery = f"""Focus on Micro-Pacing & Narrative Dynamics.
            RULES:
            1. 'type' MUST be exactly "Coach"
            2. 'color' MUST be exactly "#1E90FF"
            TARGETS: Pacing imbalances. Identify if action is rushed, or if slow atmospheric moments lack emotional purpose. Acknowledge when a drop in tension is a necessary "breathing beat" versus a dragging distraction.
            Use Context: {narrative_context}.
            OUTPUT: "critique" must be a deep insight into the narrative arc.
            Count: top {limit}. 
            Output JSON: {{ "suggestions": [{{ "type": "Coach", "original": "...", "suggested": "", "critique": "This paragraph slows the pacing right before the climax.", "color": "#1E90FF" }}] }}"""

        elif active_tool == "red_flags":
            task_discovery = f"""You are a Logic and Continuity Specialist.
            TASK: Scan the manuscript for <user_flag id="X"> tags. 
            INSTRUCTIONS:
            1. If the text inside the tag is a question, answer it. If it is narrative, perform a "Logic Stress Test."
            2. VERBATIM REQUIREMENT: The 'original' field MUST be the exact, word-for-word text found inside the <user_flag> tag. DO NOT summarize or describe the text.
            3. FIXATION: Even if the logic is sound, you MUST return a suggestion using the provided ID to confirm your analysis.
            4. STRICT FORMATTING: 
               - 'type' MUST be exactly "User Flag"
               - 'color' MUST be exactly "#d93025"
            Output JSON: {{ "suggestions": [{{ "id": "1", "type": "User Flag", "original": "verbatim text...", "suggested": "...", "critique": "...", "color": "#d93025" }}] }}"""

    return {
        "sys_prompt": sys_prompt,
        "task_discovery": task_discovery,
        "idx_task": idx_task
    }


# ==============================================================================
# ADJUDICATOR: COMPOUND OVERLAP SYNTHESIS
# ==============================================================================

def get_adjudicator_prompts(ai_model: str, manuscript_snippet: str, critiques_list: str) -> dict:
    """
    Returns sys_syn and base_prompt for the Adjudicator compound synthesis.
    """
    sys_syn = "You are a professional synthesis editor. Output JSON."
    base_prompt = f"""Act as the Chief Copy Editor. You are merging multiple overlapping mechanical critiques.
    TEXT SEGMENT: "{manuscript_snippet}"
    
    CRITIQUES TO SYNTHESIZE:
    {critiques_list}
    
    STRICT SYNTHESIS RULES:
    1. GRAMMAR/PUNCTUATION: Ensure objective correctness. Preserve capitalization unless it is the error.
    2. WORDINESS: Be concise, but DO NOT ghostwrite or invent new details.
    3. FIDELITY: Your suggested fix MUST be a direct replacement for the segment provided. To prevent partial deletions, your suggested fix must mathematically mirror the original text snippet in scope.
    
    OUTPUT JSON:
    {{
      "suggested": "The combined replacement text",
      "critique": "Professional explanation of how this resolves the issues."
    }}"""

    return {"sys_syn": sys_syn, "base_prompt": base_prompt}