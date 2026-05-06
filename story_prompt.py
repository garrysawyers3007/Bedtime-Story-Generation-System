def categorize_request(request: dict) -> dict:
    request_text = str(request.get("request", "")).lower()
    mood = str(request.get("mood", "calming")).lower()
    lesson = str(request.get("lesson", "none")).lower()
    combined_text = f"{request_text} {mood} {lesson}"

    category_keywords = {
        "friendship": {"friend", "friendship", "lonely", "share", "kindness", "together"},
        "adventure": {"adventure", "journey", "explore", "lost", "quest", "travel"},
        "magical_discovery": {
            "magic",
            "magical",
            "moon",
            "dragon",
            "fairy",
            "robot",
            "talking animal",
        },
        "learning_or_growth": {"learn", "practice", "school", "mistake", "patience", "grow"},
        "comfort_or_bedtime": {"sleep", "bedtime", "night", "afraid", "worried", "comfort"},
        "problem_solving": {"fix", "build", "solve", "help", "broken", "repair"},
    }

    scores = {category: 0 for category in category_keywords}
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in combined_text:
                scores[category] += 1

    if mood == "calming":
        scores["comfort_or_bedtime"] += 1
    elif mood == "adventurous":
        scores["adventure"] += 1
    elif mood == "magical":
        scores["magical_discovery"] += 1
    elif mood == "educational":
        scores["learning_or_growth"] += 1

    priority_order = [
        "comfort_or_bedtime",
        "problem_solving",
        "learning_or_growth",
        "friendship",
        "magical_discovery",
        "adventure",
    ]

    best_score = max(scores.values()) if scores else 0
    if best_score <= 0:
        category = "general"
    else:
        top_categories = [name for name, score in scores.items() if score == best_score]
        category = next((name for name in priority_order if name in top_categories), "general")

    strategy_map = {
        "friendship": {
            "story_strategy": "Focus on relationship growth through kind actions, listening, and sharing.",
            "arc_guidance": "Show two characters moving from a small disconnect toward trust and warmth.",
            "risk_notes": [
                "Avoid preachy friendship lectures.",
                "Use specific moments of care instead of generic teamwork lines.",
            ],
        },
        "adventure": {
            "story_strategy": "Use gentle exploration and curiosity with low stakes and safe surroundings.",
            "arc_guidance": "Let discovery drive the plot while keeping tension mild and bedtime-safe.",
            "risk_notes": [
                "Avoid danger escalation or urgent rescue framing.",
                "Keep emotional rhythm calm by the ending.",
            ],
        },
        "magical_discovery": {
            "story_strategy": "Make magic specific, grounded, and calming through concrete details.",
            "arc_guidance": "Reveal one magical detail at a time and connect each reveal to character choices.",
            "risk_notes": [
                "Avoid vague magical clichés.",
                "Keep magical events soothing, not overwhelming.",
            ],
        },
        "learning_or_growth": {
            "story_strategy": "Show growth through actions, small attempts, and adjustment after mistakes.",
            "arc_guidance": "Let the character practice, choose, and improve through events.",
            "risk_notes": [
                "Do not directly explain the lesson.",
                "Avoid moralizing lines at the end.",
            ],
        },
        "comfort_or_bedtime": {
            "story_strategy": "Prioritize reassurance, warmth, and soft sensory details throughout.",
            "arc_guidance": "Turn a small worry into calm confidence with gentle support.",
            "risk_notes": [
                "Avoid fear-heavy language.",
                "End with a concrete soothing image from the story world.",
            ],
        },
        "problem_solving": {
            "story_strategy": "Center the plot on a thoughtful choice and a gentle step-by-step solution.",
            "arc_guidance": "Introduce one clear problem, then show attempts, adjustment, and calm resolution.",
            "risk_notes": [
                "Avoid instant perfect solutions.",
                "Keep the problem low-stakes and emotionally safe.",
            ],
        },
        "general": {
            "story_strategy": "Use a simple bedtime structure with warmth, clarity, and specific details.",
            "arc_guidance": "Follow a clear beginning-middle-end with one meaningful character choice.",
            "risk_notes": [
                "Avoid generic endings and moralizing.",
                "Keep tension gentle and calming by the close.",
            ],
        },
    }

    strategy = strategy_map.get(category, strategy_map["general"])
    return {
        "category": category,
        "story_strategy": strategy["story_strategy"],
        "arc_guidance": strategy["arc_guidance"],
        "risk_notes": strategy["risk_notes"],
    }


def build_story_prompt(request: dict) -> str:
    length_guidance = {
        "short": "around 300-500 words",
        "medium": "around 600-900 words",
        "long": "around 1000-1300 words",
    }

    desired_length = request.get("length", "medium")
    target_length = length_guidance.get(desired_length, length_guidance["medium"])
    category_info = categorize_request(request)
    risk_notes_text = "\n".join([f"- {note}" for note in category_info.get("risk_notes", [])])

    lesson = request.get("lesson", "none")
    lesson_text = lesson if lesson and lesson != "none" else "No specific lesson is required."

    return (
        "You are a thoughtful bedtime storyteller writing for children ages 5-10.\n\n"
        "Write one complete bedtime story using the preferences below.\n"
        "Preferences:\n"
        f"- Story idea: {request.get('request', '')}\n"
        f"- Child age: {request.get('child_age', 7)}\n"
        f"- Desired length: {desired_length} ({target_length})\n"
        f"- Mood: {request.get('mood', 'calming')}\n"
        f"- Lesson/message: {lesson_text}\n\n"
        "Tailored strategy:\n"
        f"- Category: {category_info.get('category', 'general')}\n"
        f"- Story strategy: {category_info.get('story_strategy', '')}\n"
        f"- Arc guidance: {category_info.get('arc_guidance', '')}\n"
        "- Risk notes:\n"
        f"{risk_notes_text}\n\n"
        "Requirements:\n"
        "- Use age-appropriate language and simple vocabulary for the child age above.\n"
        "- Keep a warm, safe, non-scary tone throughout.\n"
        "- Include a clear beginning, middle, and end.\n"
        "- Include one or two memorable characters.\n"
        "- The main character should make one meaningful choice that changes what happens next.\n"
        "- If a lesson/message is provided, show it through plot events and character actions instead of explaining it directly.\n"
        "- Avoid direct moralizing phrases such as 'the moral of the story,' 'remember that,' 'dear child,' or 'learned an important lesson.'\n"
        "- Add 2-3 specific sensory details tied to this particular story (for example: sound, texture, color, or a small concrete action).\n"
        "- Include gentle conflict only, without intense danger.\n"
        "- Keep conflict low-stakes and gentle; avoid panic, danger, fear-heavy urgency, or scary imagery.\n"
        "- Avoid generic bedtime endings such as 'Goodnight, sweet dreams' or 'heart full of joy.'\n"
        "- End with a concrete calming image from the story world (for example: a soft sound fading, a small light dimming, an object resting, or a character settling peacefully).\n"
        "- Story arc to follow:\n"
        "  Beginning: introduce character, setting, and want.\n"
        "  Middle: introduce a gentle problem or curiosity.\n"
        "  Choice: main character makes one meaningful choice.\n"
        "  Ending: resolve the problem with a calm, story-specific bedtime image.\n"
        "- Do not include violence, medical advice, adult themes, or frightening content.\n\n"
        "Output format rules:\n"
        "- Start directly with the story itself.\n"
        "- Do not add setup lines like 'Here is a bedtime story' or 'Let me tell you a story.'\n"
        "- Do not write a framing scene about someone narrating or telling a story.\n"
        "- Do not include commentary, explanation, analysis, or a closing note outside the story.\n\n"
        "Output only the bedtime story body."
    )
