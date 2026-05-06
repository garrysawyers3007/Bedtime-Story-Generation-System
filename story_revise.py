def build_revision_prompt(request: dict, story: str, judge_result: dict) -> str:
    issues = judge_result.get("issues", [])
    suggestions = judge_result.get("revision_suggestions", [])

    if not issues:
        llm_issues = judge_result.get("llm_judge", {}).get("issues", [])
        rule_blocking_issues = judge_result.get("rule_check", {}).get("blocking_issues", [])
        rule_warnings = judge_result.get("rule_check", {}).get("warnings", [])
        issues = llm_issues + rule_blocking_issues + rule_warnings

    if not suggestions:
        llm_suggestions = judge_result.get("llm_judge", {}).get("revision_suggestions", [])
        rule_suggestions = judge_result.get("rule_check", {}).get("suggestions", [])
        suggestions = llm_suggestions + rule_suggestions

    overall_score = judge_result.get("llm_judge", {}).get(
        "overall_score", judge_result.get("overall_score", 0)
    )

    issues_text = "\n".join([f"  - {issue}" for issue in issues]) if issues else "  (None identified)"
    suggestions_text = "\n".join([f"  - {suggestion}" for suggestion in suggestions]) if suggestions else "  (None)"

    return (
        "You are a bedtime story reviser. Improve the following story using the judge feedback below.\n\n"
        "Original story:\n"
        f"{story}\n\n"
        "User request context:\n"
        f"- Story idea: {request.get('request', '')}\n"
        f"- Child age: {request.get('child_age', 7)}\n"
        f"- Desired mood: {request.get('mood', 'calming')}\n\n"
        "Judge feedback:\n"
        f"Overall score: {overall_score}/10\n"
        f"Issues found:\n{issues_text}\n\n"
        f"Revision suggestions:\n{suggestions_text}\n\n"
        "Revision instructions:\n"
        "1. Preserve the original user request: keep requested characters, setting, age range, mood, length, and lesson.\n"
        "2. Do not replace the premise with a completely different story.\n"
        "3. Address all identified issues and revision suggestions directly and keep fixes targeted.\n"
        "4. Add 2-3 concrete sensory details tied to this specific story world (objects, sounds, textures, colors, or small actions).\n"
        "5. Avoid generic fantasy/bedtime imagery and repeated clichés.\n"
        "6. Give the main character one clear choice that changes what happens next.\n"
        "7. Show agency through action (noticing, deciding, trying, adjusting, asking, helping, solving), not passive observation.\n"
        "8. Show the lesson through events and character choices, not direct explanation.\n"
        "9. Remove direct moralizing phrases such as: 'learned an important lesson', 'the moral of the story', 'remember that', 'dear child', 'my dear friends', 'from that day on', and 'this taught them that'.\n"
        "10. Do not explain the lesson to the reader. Let the final scene show the lesson through the character's choice and its peaceful result.\n"
        "11. Replace generic endings. Avoid closings like: 'Goodnight, sweet dreams', 'Goodnight, sleep tight', 'heart full of joy', 'heart full of warmth', 'filled with kindness', or 'anything is possible'.\n"
        "12. End with a concrete calming image from this story (for example: an object resting, a soft sound fading, a light dimming, or a character peacefully settling down).\n"
        "13. Keep conflict gentle and bedtime-safe; avoid panic, danger, fear-heavy urgency, or scary imagery.\n"
        "14. If the story feels urgent or stressful, lower the stakes while keeping the same core problem. The revised version should feel like a bedtime story, not a rescue mission.\n"
        "15. If there is tension, soften it into concern, curiosity, or a small problem.\n"
        "16. Keep the revised output within the requested length range and avoid unnecessary expansion.\n"
        f"17. Use language appropriate for age {request.get('child_age', 7)}.\n\n"
        "Output only the revised story text, no commentary or explanation."
    )


def revise_story(request: dict, story: str, judge_result: dict) -> str:
    from main import call_model, REVISION_TEMPERATURE

    prompt = build_revision_prompt(request, story, judge_result)
    return call_model(prompt, temperature=REVISION_TEMPERATURE)


def revise_story_with_user_feedback(request: dict, story: str, user_feedback: str) -> str:
    from main import call_model, REVISION_TEMPERATURE

    prompt = (
        "You are a bedtime story reviser. Revise the story based on the user's requested changes.\n\n"
        "Original story:\n"
        f"{story}\n\n"
        "Original request context (must remain consistent):\n"
        f"- Story idea: {request.get('request', '')}\n"
        f"- Child age: {request.get('child_age', 7)}\n"
        f"- Desired mood: {request.get('mood', 'calming')}\n"
        f"- Desired length: {request.get('length', 'medium')}\n"
        f"- Lesson/message: {request.get('lesson', 'none')}\n\n"
        "User requested changes:\n"
        f"{user_feedback}\n\n"
        "Revision instructions:\n"
        "1. Preserve the original story request, age, mood, length, and lesson.\n"
        "2. Apply the user's requested changes directly while keeping the same core story premise.\n"
        "3. Keep the story age-appropriate for children ages 5-10.\n"
        "4. Keep the story bedtime-safe and emotionally gentle.\n"
        "5. Avoid scary, violent, adult, medical, or intense content.\n"
        "6. Do not directly explain the lesson unless the user explicitly asked for direct explanation.\n"
        "7. Keep the final output as only the revised story text.\n\n"
        "Output only the revised story text, no commentary or explanation."
    )
    return call_model(prompt, temperature=REVISION_TEMPERATURE)
