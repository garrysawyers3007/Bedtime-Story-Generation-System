import re


ALLOWED_MOODS = {"calming", "funny", "adventurous", "magical", "educational"}

UNSAFE_PHRASES = [
    "sexual",
    "sexy",
    "horny",
    "hook up",
    "hooking up",
    "affair",
    "adult",
    "porn",
    "explicit",
    "erotic",
    "violence",
    "blood",
    "gore",
    "kill",
    "murder",
    "weapon",
    "horror",
    "nightmare",
    "terrifying",
    "drug",
    "alcohol",
    "medical",
    "hospital",
    "surgery",
    "diagnosis",
    "disease",
]

PUBLIC_FIGURE_TERMS = [
    "president",
    "prime minister",
    "senator",
    "governor",
    "politician",
    "celebrity",
    "public figure",
    "famous actor",
    "real person",
]

SCANDAL_TERMS = [
    "scandal",
    "affair",
    "hook up",
    "hooking up",
    "adult relationship",
]


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = " ".join(text.lower().split())
    normalized_phrase = " ".join(phrase.lower().split())
    if " " not in normalized_phrase:
        return bool(re.search(rf"\b{re.escape(normalized_phrase)}\b", normalized_text))
    return normalized_phrase in normalized_text


def _validate_child_safe_text(text: str, mood_text: str = "") -> tuple[bool, str]:
    normalized_text = " ".join(text.lower().split())
    normalized_mood = " ".join(mood_text.lower().split())

    for phrase in UNSAFE_PHRASES:
        if _contains_phrase(normalized_text, phrase) or _contains_phrase(normalized_mood, phrase):
            return False, f"Request includes age-inappropriate content related to '{phrase}'."

    has_public_figure = any(_contains_phrase(normalized_text, term) for term in PUBLIC_FIGURE_TERMS)
    has_scandal_theme = any(_contains_phrase(normalized_text, term) for term in SCANDAL_TERMS)
    if has_public_figure and has_scandal_theme:
        return False, "Request includes adult public-figure or scandal themes that are not suitable for a children's bedtime story."

    return True, ""


def validate_initial_request(request: dict) -> tuple[bool, str]:
    request_text = str(request.get("request", ""))
    lesson_text = str(request.get("lesson", ""))
    mood_text = str(request.get("raw_mood", request.get("mood", "")))

    is_safe, reason = _validate_child_safe_text(
        f"{request_text}\n{lesson_text}",
        mood_text,
    )
    if not is_safe:
        return False, reason

    return True, ""


def validate_user_feedback(user_feedback: str) -> tuple[bool, str]:
    return _validate_child_safe_text(user_feedback)