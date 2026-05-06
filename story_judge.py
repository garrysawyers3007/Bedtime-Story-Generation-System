import json
import re


GENERIC_PHRASES = [
    "hearts full of love and friendship",
    "bond that could never be broken",
    "happiest trio in the whole wide world",
    "magical adventure",
    "twinkling stars",
    "sweet dreams",
    "power of friendship",
    "from that day on",
]

PASSIVE_OR_PRESENCE_PHRASES = [
    "was there",
    "stood beside",
    "walked along",
    "watched",
    "followed",
    "sat quietly",
]

MEANINGFUL_ACTION_STEMS = [
    "notice",
    "decide",
    "choose",
    "chose",
    "try",
    "help",
    "fix",
    "make",
    "made",
    "ask",
    "gather",
    "create",
    "build",
    "built",
    "repair",
    "guide",
    "learn",
    "return",
    "paint",
    "blend",
    "solve",
]

OLDER_CHILD_PROBLEM_SIGNALS = [
    "problem",
    "lost",
    "confused",
    "stuck",
    "broken",
    "missing",
    "forgot",
    "unsure",
    "needed",
    "challenge",
    "difficult",
    "wrong",
    "changed",
]

OLDER_CHILD_RESOLUTION_SIGNALS = [
    "noticed",
    "decided",
    "tried",
    "helped",
    "solved",
    "remembered",
    "adjusted",
    "built",
    "fixed",
    "guided",
    "asked",
    "listened",
    "shared",
]

GENERIC_CLICHES = [
    "magical land",
    "enchanted forest",
    "twinkling stars",
    "power of friendship",
    "happily ever after",
    "heart full of joy",
    "from that day on",
    "sweet dreams",
    "magical adventure",
]

INTENSE_BEDTIME_TERMS = [
    "panic",
    "panicked",
    "terrified",
    "horror",
    "frightening",
    "screamed",
    "tears welled up",
    "about to give up",
    "heart raced",
    "dull and lifeless",
    "shadow over the town",
    "nightmare",
    "dangerous",
    "attacked",
    "trapped",
    "before it was too late",
    "death",
]

LECTURING_PHRASES = [
    "learned an important lesson",
    "valuable lesson",
    "teaching her this lesson",
    "the moral of the story",
    "remember that",
    "you should always",
    "my dear friends",
    "this taught them that",
    "even the biggest mistakes",
    "with a little patience and a lot of love",
    "dear child",
]

GENERIC_ENDING_PHRASES = [
    "goodnight, sweet dreams",
    "heart full of gratitude",
    "magic of the moon and stars",
    "drift off to sleep",
    "the end",
]

REQUEST_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "about",
    "story",
    "named",
    "name",
    "with",
    "who",
    "that",
    "happens",
    "to",
    "be",
    "of",
    "in",
    "on",
    "for",
    "at",
    "from",
    "into",
    "is",
    "are",
    "was",
    "were",
    "their",
    "his",
    "her",
    "they",
    "them",
    "best",
    "friend",
}


def build_judge_prompt(request: dict, story: str) -> str:
    story_idea = request.get("request", "")
    child_age = request.get("child_age", 7)
    mood = request.get("mood", "calming")
    lesson = request.get("lesson", "none")

    age_guidance = (
        "For age 5-7: simpler vocabulary, shorter sentences, clearer moral, predictable plot.\n"
        if child_age <= 7
        else "For age 8-10: richer imagery, layered plot, more sophisticated language, but still bedtime-safe.\n"
    )

    return (
        "You are a STRICT bedtime story evaluator for children ages 5-10. Be critical and demanding.\n"
        "Evaluate the story using the detailed criteria below and score conservatively.\n"
        "Before assigning scores, carefully evaluate the story against each criterion: age appropriateness, bedtime suitability, creativity, coherence, and request adherence. Use that evaluation to decide the scores.\n"
        "Do not include chain-of-thought or long reasoning in the output. Return only the requested JSON. Put any important conclusions into the concise issues and revision_suggestions fields.\n"
        "When listing issues, make them specific and evidence-based. For example, mention if the story has intense bedtime language, direct moralizing, missing requested elements, passive characters, generic phrasing, or continuity problems.\n"
        "Do not reward length by itself. A short story can score highly if it is complete, warm, age-appropriate, and coherent. A long story should not score highly if it is generic, repetitive, or unfocused.\n"
        "If the story contains clearly unsafe or age-inappropriate content, it should fail regardless of creativity or coherence.\n"
        "Return ONLY valid JSON, no preamble or explanation.\n\n"
        "Story to evaluate:\n"
        f"{story}\n\n"
        "User request context:\n"
        f"- Story idea: {story_idea}\n"
        f"- Child age: {child_age}\n"
        f"- Desired mood: {mood}\n"
        f"- Lesson/message: {lesson}\n\n"
        "DETAILED EVALUATION CRITERIA:\n\n"
        "1. BEDTIME SAFETY (bedtime_suitability score):\n"
        "   Rate 9-10: No scary, violent, medical, or adult content. Panic, fear-heavy language, nightmares, "
        "danger, separation anxiety, or intense emotion are ABSENT. Ending is calm and genuinely comforting.\n"
        "   Rate 7-8: Mostly safe but has minor elements that could cause mild unease. Minor tension but nothing intense.\n"
        "   Rate 5-6: Some elements that don't fit bedtime (mildly scary scenes, intense emotion, or ambiguous ending).\n"
        "   Rate 1-4: Contains scary, violent, or disturbing content. NOT bedtime-appropriate.\n"
        "   Flag MAJOR ISSUE if any scary/violent/adult/medical content is present.\n\n"
        "2. AGE APPROPRIATENESS (age_appropriateness score):\n"
        f"   {age_guidance}"
        "   Rate 9-10: Vocabulary and concepts match the child age perfectly. Clear moral or lesson if present.\n"
        "   Rate 7-8: Mostly age-appropriate but some words or concepts feel slightly off.\n"
        "   Rate 5-6: Some parts are too simple or too complex for the age.\n"
        "   Rate 1-4: Major vocabulary or concept mismatches for the age.\n\n"
        "3. STORY QUALITY (coherence score):\n"
        "   Must have: clear beginning, middle, and end.\n"
        "   Must have: the main character makes at least one meaningful choice or faces meaningful conflict.\n"
        "   Must have: gentle conflict or curiosity driving the plot (not just random events).\n"
        "   Must have: the ending resolves the emotional arc or story tension.\n"
        "   Check for simple continuity consistency (for example: an object left behind should not later appear with the character unless explained, and character actions should not contradict earlier events).\n"
        "   If there is a minor continuity issue, reduce coherence by 1 point and add a specific issue describing the inconsistency.\n"
        "   Rate 9-10: All elements present and well-executed. Engaging and satisfying.\n"
        "   Rate 7-8: All elements present but somewhat predictable or flat.\n"
        "   Rate 5-6: One or more elements missing or weakly developed.\n"
        "   Rate 1-4: No clear structure or emotional arc.\n\n"
        "4. CREATIVITY (creativity score):\n"
        "   A story should NOT receive 9 or 10 for creativity unless it has:\n"
        "   - A specific, memorable premise\n"
        "   - At least two concrete details that feel unique to this story\n"
        "   - At least one main character who notices, suggests, solves, remembers, decides, discovers, helps, or figures something out in a meaningful way\n"
        "   - A gentle but real story arc, not just a sequence of pleasant events\n"
        "   - Language that avoids generic bedtime clichés\n"
        "   Generic phrases should reduce creativity score, including:\n"
        "   - 'hearts full of love and friendship'\n"
        "   - 'bond that could never be broken'\n"
        "   - 'happiest trio in the whole wide world'\n"
        "   - 'magical adventure'\n"
        "   - 'twinkling stars'\n"
        "   - 'sweet dreams'\n"
        "   - 'power of friendship'\n"
        "   - 'from that day on'\n"
        "   Rate 9-10: Highly memorable with a fresh premise, specific unique details, active character choices, and no cliché-heavy language.\n"
        "   Rate 7-8: Good and safe, but somewhat familiar or predictable.\n"
        "   Rate 5-6: Understandable but generic, repetitive, or mostly a sequence of pleasant events.\n"
        "   Rate 1-4: Poor fit, confusing, or not engaging.\n"
        "   Rate lower when main characters are passive observers instead of meaningful contributors.\n\n"
        "OVERALL SCORING GUARDRAILS:\n"
        "- Overall score should NOT be higher than creativity if the story feels generic.\n"
        "- Overall score should NOT be 9 or 10 unless the story is both safe and memorable.\n"
        "- Bedtime safety alone is not enough for a 9.\n"
        "- For bedtime_suitability to be 9, the story should have calm emotional rhythm and a specific soothing ending image.\n"
        "- A story with clear beginning, middle, and end can score coherence 8.\n"
        "- Coherence 9-10 requires an especially clear and satisfying emotional arc, not just structure.\n\n"
        "5. REQUEST ADHERENCE (scored as part of overall pass/fail):\n"
        "   Flag MAJOR ISSUE if:\n"
        "   - Main characters or setting from the request are missing or replaced.\n"
        "   - Length significantly mismatches the user request (short ≠ 300-500 words, etc.).\n"
        "   - Mood contradicts user request (e.g., user wants calming but story is scary or hilarious).\n\n"
        "SCORING SCALE (apply to all criteria):\n"
        "- 9-10: Excellent, memorable, would delight a child at bedtime.\n"
        "- 7-8: Good quality but somewhat generic or has minor issues.\n"
        "- 5-6: Acceptable but needs revision to be truly good.\n"
        "- 1-4: Poor; significant issues that need fixing.\n\n"
        "CALIBRATION INSTRUCTION:\n"
        "- Be honest and conservative. Most acceptable stories should score 7-8.\n"
        "- Reserve 9-10 for truly excellent stories only.\n\n"
        "PASS CRITERIA (all must be true):\n"
        "- overall_score >= 8 (high quality overall)\n"
        "- bedtime_suitability >= 8 (must be safe and calming)\n"
        "- age_appropriateness >= 8 (must fit the child's age well)\n"
        "- coherence >= 8 (must have clear structure and emotional arc)\n"
        "- creativity >= 7 (must be sufficiently specific and not overly generic)\n"
        "- NO major safety issues\n"
        "- Request adherence met (characters/theme, mood, length)\n\n"
        "Return ONLY this JSON structure:\n"
        '{"passes": true/false, "overall_score": <1-10>, "age_appropriateness": <1-10>, '
        '"bedtime_suitability": <1-10>, "creativity": <1-10>, "coherence": <1-10>, '
        '"issues": ["specific issue 1", "specific issue 2"], '
        '"revision_suggestions": ["specific suggestion 1", "specific suggestion 2"]}'
    )


def _get_int_score(result: dict, key: str) -> int:
    value = result.get(key, 0)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _contains_major_safety_issue(issues: list[str]) -> bool:
    safety_keywords = [
        "major safety",
        "scary",
        "violent",
        "disturbing",
        "adult",
        "medical",
        "not bedtime-appropriate",
    ]
    for issue in issues:
        lowered = str(issue).lower()
        if any(keyword in lowered for keyword in safety_keywords):
            return True
    return False


def _normalize_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = " ".join(text.lower().split())
    normalized_phrase = " ".join(phrase.lower().split())

    if " " not in normalized_phrase:
        return bool(re.search(rf"\b{re.escape(normalized_phrase)}\b", normalized_text))

    return normalized_phrase in normalized_text


def _extract_request_entities(request_text: str) -> tuple[list[str], list[str]]:
    capitalized_names = re.findall(r"\b[A-Z][a-z]{2,}\b", request_text)
    unique_names = []
    for name in capitalized_names:
        if name.lower() not in {"what", "when", "where"} and name not in unique_names:
            unique_names.append(name)

    tokens = re.findall(r"\b[a-z]{4,}\b", request_text.lower())
    keywords = []
    for token in tokens:
        if token in REQUEST_STOPWORDS:
            continue
        if token not in keywords:
            keywords.append(token)
    return unique_names[:5], keywords[:8]


def _find_likely_story_names(story: str) -> list[str]:
    name_counts: dict[str, int] = {}
    for match in re.findall(r"\b[A-Z][a-z]{2,}\b", story):
        lowered = match.lower()
        if lowered in {"the", "and", "once", "night", "moon"}:
            continue
        name_counts[match] = name_counts.get(match, 0) + 1
    frequent_names = [name for name, count in name_counts.items() if count >= 2]
    return frequent_names[:5]


def _sentence_stats(story: str) -> tuple[float, float]:
    sentences = [s.strip() for s in re.split(r"[.!?]+", story) if s.strip()]
    words = re.findall(r"\b\w+\b", story)
    if not sentences:
        return 0.0, 0.0
    avg_words_per_sentence = len(words) / len(sentences)
    long_word_ratio = 0.0
    if words:
        long_words = [w for w in words if len(w) >= 8]
        long_word_ratio = len(long_words) / len(words)
    return avg_words_per_sentence, long_word_ratio


def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"\b[a-z']+\b", text.lower())


def _has_action_stem(word: str) -> bool:
    for stem in MEANINGFUL_ACTION_STEMS:
        if word == stem:
            return True
        if word.startswith(stem) and len(word) <= len(stem) + 3:
            return True
    return False


def _contains_any_signal(text: str, signals: list[str]) -> bool:
    return any(_contains_phrase(text, signal) for signal in signals)


def _count_characters_with_meaningful_action(story: str, likely_names: list[str], window: int = 8) -> int:
    words = _tokenize_words(story)
    if not words:
        return 0

    contributing_names: set[str] = set()
    name_set = {name.lower() for name in likely_names}
    for idx, word in enumerate(words):
        if word not in name_set:
            continue
        start = max(0, idx - window)
        end = min(len(words), idx + window + 1)
        if any(_has_action_stem(candidate) for candidate in words[start:end]):
            contributing_names.add(word)
    return len(contributing_names)


def _character_has_meaningful_action(story: str, likely_names: list[str], window: int = 8) -> bool:
    if likely_names:
        return _count_characters_with_meaningful_action(story, likely_names, window) > 0

    words = _tokenize_words(story)
    fallback_names = {"he", "she", "they", "someone", "child", "kid"}
    for idx, word in enumerate(words):
        if word not in fallback_names:
            continue
        start = max(0, idx - window)
        end = min(len(words), idx + window + 1)
        if any(_has_action_stem(candidate) for candidate in words[start:end]):
            return True
    return False


def run_rule_based_checks(request: dict, story: str) -> dict:
    blocking_issues: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    request_text = str(request.get("request", ""))
    lesson = str(request.get("lesson", "none")).strip().lower()
    child_age = int(request.get("child_age", 7) or 7)
    mood = str(request.get("mood", "calming")).strip().lower()

    lowered_story = story.lower()

    # 1) Request adherence: ensure major requested entities appear in the story.
    request_names, request_keywords = _extract_request_entities(request_text)
    matched_names = [name for name in request_names if re.search(rf"\b{re.escape(name.lower())}\b", lowered_story)]
    matched_keywords = [kw for kw in request_keywords if re.search(rf"\b{re.escape(kw)}\b", lowered_story)]

    missing_major_elements = False
    if request_names and len(matched_names) < max(1, len(request_names) - 1):
        missing_major_elements = True
    if request_keywords and len(matched_keywords) < max(1, len(request_keywords) // 3):
        missing_major_elements = True
    if missing_major_elements:
        blocking_issues.append("Story is missing major requested characters or key request elements.")
        suggestions.append("Reintroduce the most important requested characters and themes directly in story events.")

    # 2) Character agency: at least one likely main character should take meaningful action.
    likely_story_names = _find_likely_story_names(story)
    likely_main_names = []
    for name in request_names + likely_story_names:
        if name not in likely_main_names:
            likely_main_names.append(name)

    has_active_agency = _character_has_meaningful_action(story, likely_main_names, window=8)
    contributing_character_count = _count_characters_with_meaningful_action(
        story, likely_main_names, window=8
    )
    too_simple_for_older_children = False

    agency_arc_signals = {
        "noticed_problem": bool(re.search(r"\b(notice|noticed|notices|saw|found|realized)\b", lowered_story)),
        "made_choice": bool(re.search(r"\b(decide|decided|decides|choose|chose|chooses|made)\b", lowered_story)),
        "attempted_solution": bool(re.search(r"\b(try|tried|tries|fix|fixed|fixes|solve|solved|solves|build|built|repair|repaired)\b", lowered_story)),
        "accepted_help": bool(re.search(r"\b(ask|asked|asks|help|helped|helps|together|with\s+.*help)\b", lowered_story)),
        "changed_outcome": bool(re.search(r"\b(finally|at last|worked|solved|better|calm|safe|succeeded|returned)\b", lowered_story)),
    }
    demonstrates_complete_agency_arc = sum(1 for value in agency_arc_signals.values() if value) >= 4

    has_no_detectable_agency = not has_active_agency and not demonstrates_complete_agency_arc

    passive_pattern = re.compile(
        r"\b(?:"
        + "|".join(re.escape(word) for word in PASSIVE_OR_PRESENCE_PHRASES)
        + r")\b",
        flags=re.IGNORECASE,
    )
    has_passive_presence = bool(passive_pattern.search(story))
    if has_no_detectable_agency:
        if has_passive_presence:
            blocking_issues.append("No clear main-character agency detected; characters seem mostly present without meaningful action.")
        else:
            blocking_issues.append("No clear main-character agency detected in the story events.")
        suggestions.append(
            "Show a protagonist noticing a problem, choosing a response, attempting a fix, accepting help if needed, and changing the outcome."
        )
    elif not has_active_agency:
        suggestions.append(
            "Character agency appears somewhat indirect; make at least one meaningful action more explicit near the main character."
        )

    # 3) Generic phrasing: soft signal unless very high.
    matched_generic_phrases = [phrase for phrase in GENERIC_CLICHES if _contains_phrase(story, phrase)]
    generic_phrase_count = len(matched_generic_phrases)
    has_very_high_genericity = generic_phrase_count >= 4
    if generic_phrase_count >= 2:
        if has_very_high_genericity:
            blocking_issues.append("Story relies heavily on generic bedtime/fantasy clichés and feels formulaic.")
        else:
            warnings.append("Story may feel somewhat generic; replace repeated clichés with specific sensory details and fresh moments.")
        suggestions.append(
            f"Reduce cliché phrasing. Matched phrases: {', '.join(matched_generic_phrases[:6])}."
        )

    # 4) Bedtime safety and emotional intensity.
    matched_intense_terms = [
        term
        for term in INTENSE_BEDTIME_TERMS
        if _contains_phrase(story, term)
    ]

    strong_intensity_terms = {
        "panic",
        "panicked",
        "terrified",
        "horror",
        "frightening",
        "screamed",
        "tears welled up",
        "about to give up",
        "heart raced",
        "dull and lifeless",
        "shadow over the town",
        "dangerous",
        "trapped",
        "attacked",
        "nightmare",
        "death",
        "before it was too late",
    }
    matched_strong_intensity = [term for term in matched_intense_terms if term in strong_intensity_terms]

    if mood == "calming":
        safety_issue = len(matched_strong_intensity) >= 1
    elif mood in {"adventurous", "magical"}:
        safety_issue = len(matched_strong_intensity) >= 2
    else:
        safety_issue = len(matched_strong_intensity) >= 1

    if safety_issue:
        blocking_issues.append(
            "Conflict may be too intense for bedtime due to scary or high-intensity wording."
        )
        suggestions.append(
            "Keep conflict gentle and reassuring; replace intense language with calmer stakes and comforting resolution."
        )
        suggestions.append(
            "Soften tension with calmer language, for example: 'Mira took a slow breath', 'The moon looked softer than usual', 'She felt worried, but not alone', or 'They worked carefully'."
        )

    # 5) Moral delivery: prefer demonstrated lesson over direct lecture.
    has_requested_lesson = lesson not in {"", "none", "no", "n/a"}
    lecture_phrase_found = [phrase for phrase in LECTURING_PHRASES if _contains_phrase(story, phrase)]
    if has_requested_lesson:
        lesson_signal_words = ["because", "so", "after", "then", "chose", "decided", "learned"]
        has_event_based_lesson_signal = any(word in lowered_story for word in lesson_signal_words)
        if not has_event_based_lesson_signal:
            suggestions.append(
                "Demonstrate the lesson through character choices and consequences, not just statements."
            )
    if lecture_phrase_found:
        warning_or_block_text = "Story directly explains the lesson instead of showing it through plot and character choices."
        if has_requested_lesson:
            blocking_issues.append(warning_or_block_text)
        else:
            warnings.append(warning_or_block_text)
        suggestions.append("Remove direct lecturing language and let the character choices reveal the lesson.")

    direct_moralizing_with_lesson = has_requested_lesson and bool(lecture_phrase_found)

    # 5b) Generic ending quality check (signal, not automatic fail).
    matched_generic_endings = [phrase for phrase in GENERIC_ENDING_PHRASES if _contains_phrase(story, phrase)]
    if matched_generic_endings:
        warnings.append("Ending may use common bedtime phrasing instead of a story-specific calm image.")
        suggestions.append(
            "Ending may feel generic; use a specific emotional closing image tied to this story's events."
        )

    # 6) Age fit heuristics.
    avg_sentence_len, long_word_ratio = _sentence_stats(story)
    has_problem_signal = any(
        phrase in lowered_story
        for phrase in ["problem", "trouble", "couldn't", "needed to", "had to", "figured out", "decided"]
    )
    if child_age <= 7:
        if avg_sentence_len > 18 or long_word_ratio > 0.18:
            warnings.append("Language may be slightly complex for ages 5-7.")
            suggestions.append("Use shorter sentences and simpler words while keeping a clear emotional arc.")
    else:
        if avg_sentence_len < 8 and not has_problem_signal:
            warnings.append("Story may be slightly simplistic for ages 8-10.")
            suggestions.append("Add slightly richer details and one specific problem solved through a meaningful choice.")

    # 6b) Older-child simplicity gate: safe stories for ages 8-10 still need a specific problem and contribution.
    if child_age >= 8:
        has_obstacle_signal = _contains_any_signal(story, OLDER_CHILD_PROBLEM_SIGNALS)
        has_resolution_signal = _contains_any_signal(story, OLDER_CHILD_RESOLUTION_SIGNALS)
        multiple_named_characters = len(likely_main_names) >= 2
        weak_distinct_contribution = multiple_named_characters and contributing_character_count < 2
        thin_teamwork_signal = _contains_phrase(story, "worked together") and weak_distinct_contribution
        no_specific_choice_signal = not bool(
            re.search(r"\b(decide|decided|decides|choose|chose|chooses|adjust|adjusted|instead|but)\b", lowered_story)
        )
        direct_lesson_without_action = has_requested_lesson and bool(lecture_phrase_found) and not has_resolution_signal

        too_simple_for_older_children = (
            (not has_obstacle_signal and not has_resolution_signal)
            or (not has_obstacle_signal and no_specific_choice_signal)
            or thin_teamwork_signal
            or weak_distinct_contribution
            or direct_lesson_without_action
        )

        if too_simple_for_older_children:
            blocking_issues.append(
                "Story may be too simple for ages 8-10; it needs a more specific problem and stronger character contribution."
            )
            suggestions.append(
                "Revise the story so the main character or characters solve a specific gentle problem through concrete actions, rather than simply stating the lesson."
            )

    # Mood fit as a soft cue for calm bedtime quality.
    if mood == "calming" and any(term in lowered_story for term in ["chase", "fight", "shout", "argue"]):
        suggestions.append("For a calming mood, reduce high-energy conflict words and end with gentle reassurance.")

    checks_passed = not any(
        [
            safety_issue,
            missing_major_elements,
            has_no_detectable_agency,
            has_very_high_genericity,
            direct_moralizing_with_lesson,
            too_simple_for_older_children,
        ]
    )
    return {
        "passes": checks_passed,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "suggestions": suggestions,
    }


def judge_story(request: dict, story: str) -> dict:
    from main import call_model, JUDGE_TEMPERATURE

    prompt = build_judge_prompt(request, story)
    response = call_model(prompt, temperature=JUDGE_TEMPERATURE)

    try:
        llm_raw_result = json.loads(response)

        if not isinstance(llm_raw_result, dict):
            raise json.JSONDecodeError("Judge response is not a JSON object.", response, 0)

        rule_result = run_rule_based_checks(request, story)

        overall_score = _get_int_score(llm_raw_result, "overall_score")
        age_appropriateness = _get_int_score(llm_raw_result, "age_appropriateness")
        bedtime_suitability = _get_int_score(llm_raw_result, "bedtime_suitability")
        creativity = _get_int_score(llm_raw_result, "creativity")
        coherence = _get_int_score(llm_raw_result, "coherence")

        llm_issues = _normalize_list(llm_raw_result.get("issues", []))
        llm_suggestions = _normalize_list(llm_raw_result.get("revision_suggestions", []))

        llm_passes = all(
            [
                overall_score >= 8,
                bedtime_suitability >= 8,
                age_appropriateness >= 8,
                coherence >= 8,
                creativity >= 7,
            ]
        )
        has_major_safety_issue = _contains_major_safety_issue(llm_issues)
        llm_passes = llm_passes and not has_major_safety_issue

        rule_passes = bool(rule_result.get("passes", False))
        accepted = llm_passes and rule_passes

        if accepted:
            revision_trigger = "none"
        elif not llm_passes and not rule_passes:
            revision_trigger = "both"
        elif not llm_passes:
            revision_trigger = "llm_judge"
        else:
            revision_trigger = "rule_based_check"

        rule_blocking_issues = _normalize_list(rule_result.get("blocking_issues", []))
        rule_warnings = _normalize_list(rule_result.get("warnings", []))
        rule_suggestions = _normalize_list(rule_result.get("suggestions", []))
        combined_issues = llm_issues + rule_blocking_issues + rule_warnings
        combined_suggestions = llm_suggestions + rule_suggestions

        return {
            "llm_judge": {
                "passes": llm_passes,
                "overall_score": overall_score,
                "age_appropriateness": age_appropriateness,
                "bedtime_suitability": bedtime_suitability,
                "creativity": creativity,
                "coherence": coherence,
                "issues": llm_issues,
                "revision_suggestions": llm_suggestions,
            },
            "rule_check": {
                "passes": rule_passes,
                "blocking_issues": rule_blocking_issues,
                "warnings": rule_warnings,
                "suggestions": rule_suggestions,
            },
            "accepted": accepted,
            "revision_status": "accepted" if accepted else "needs_revision",
            "revision_trigger": revision_trigger,
            "issues": combined_issues,
            "revision_suggestions": combined_suggestions,
        }
    except json.JSONDecodeError:
        return {
            "llm_judge": {
                "passes": False,
                "overall_score": 0,
                "age_appropriateness": 0,
                "bedtime_suitability": 0,
                "creativity": 0,
                "coherence": 0,
                "issues": ["Judge response was not valid JSON."],
                "revision_suggestions": [],
            },
            "rule_check": {
                "passes": False,
                "blocking_issues": ["Rule-based check skipped because judge JSON parsing failed."],
                "warnings": [],
                "suggestions": [],
            },
            "accepted": False,
            "revision_status": "needs_revision",
            "revision_trigger": "llm_judge",
            "issues": ["Judge response was not valid JSON."],
            "revision_suggestions": [],
        }
