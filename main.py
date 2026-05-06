import argparse
import os
import sys
import time
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError
from safety import validate_initial_request, validate_user_feedback
from story_prompt import build_story_prompt
from story_judge import judge_story
from story_revise import revise_story, revise_story_with_user_feedback

# Temperature settings for different pipeline stages
# Higher temp = more creative/varied; lower temp = more focused/deterministic
STORY_TEMPERATURE = 0.6  # Story generation: higher creativity, less generic
JUDGE_TEMPERATURE = 0.0  # Judge evaluation: deterministic and consistent scoring
REVISION_TEMPERATURE = 0.3  # Revision: follow judge feedback closely while still creative

UNSAFE_CHILD_STORY_MESSAGE = (
    "I can’t create that as a children’s bedtime story. "
    "Please try a child-safe idea, such as a magical journey, "
    "animal friendship, gentle adventure, or calming bedtime story."
)

def call_model(prompt: str, max_tokens=3000, temperature=0.1) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Set it in your environment before running.")

    client = OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
    except AuthenticationError as err:
        raise RuntimeError("OpenAI authentication failed. Check OPENAI_API_KEY.") from err
    except RateLimitError as err:
        raise RuntimeError("OpenAI rate limit reached. Please try again in a moment.") from err
    except APIConnectionError as err:
        raise RuntimeError("Could not connect to OpenAI. Check your network and try again.") from err
    except APIError as err:
        raise RuntimeError("OpenAI API error occurred. Please retry.") from err

def collect_user_request() -> dict:
    request = input(
        "What kind of bedtime story do you want? "
        "(Examples: a shy dragon making friends, a moonlight forest adventure, "
        "or a brave child learning to share.) "
    ).strip()

    while True:
        child_age_input = input("Child age (default 7): ").strip()
        if not child_age_input:
            child_age = 7
            break

        try:
            child_age = int(child_age_input)
        except ValueError:
            print("Please enter a valid number for age.")
            continue

        if child_age < 5 or child_age > 10:
            print("Please enter an age between 5 and 10.")
            continue

        break

    length_options = {"short", "medium", "long"}
    length_input = input("Desired length (short, medium, or long; default medium): ").strip().lower()
    length = length_input if length_input in length_options else "medium"

    mood_options = {"calming", "funny", "adventurous", "magical", "educational"}
    mood_input = input(
        "Mood (calming, funny, adventurous, magical, or educational; default calming): "
    ).strip().lower()
    mood = mood_input if mood_input in mood_options else "calming"

    lesson_input = input("Optional lesson/message (default none): ").strip()
    lesson = lesson_input if lesson_input else "none"

    return {
        "request": request,
        "child_age": child_age,
        "length": length,
        "mood": mood,
        "raw_mood": mood_input,
        "lesson": lesson,
    }


def generate_story(request: dict) -> str:
    prompt = build_story_prompt(request)
    return call_model(prompt, temperature=STORY_TEMPERATURE)


def generate_story_with_judge_loop(request: dict, max_attempts: int = 2) -> tuple:
    """Generate a story, evaluate it, and optionally revise once.

    Returns:
        tuple[str, dict, bool]:
            - story: final story text (original or revised)
            - judge_result: structured evaluation with llm_judge/rule_check,
              accepted flag, revision_status, and revision_trigger
            - was_revised: True if a revision attempt was made, else False
    """
    story = generate_story(request)
    # judge_story() owns prompt construction and evaluation logic in story_judge.py.
    judge_result = judge_story(request, story)

    accepted = judge_result.get("accepted", False)
    initial_trigger = judge_result.get("revision_trigger", "none")

    if accepted:
        # Story passed on first attempt
        judge_result["revision_status"] = "accepted_on_first_attempt"
        judge_result["revision_trigger"] = "none"
        return (story, judge_result, False)

    # Story needs revision
    if max_attempts > 1:
        # revise_story() owns revision prompt logic in story_revise.py.
        story = revise_story(request, story, judge_result)
        # Re-judge revised output using the same judge module logic.
        judge_result = judge_story(request, story)
        judge_result["revision_status"] = (
            "accepted_after_revision" if judge_result.get("accepted", False) else "needs_revision"
        )
        judge_result["revision_trigger"] = initial_trigger if initial_trigger in {
            "llm_judge",
            "rule_based_check",
            "both",
        } else judge_result.get("revision_trigger", "none")
        return (story, judge_result, True)

    # No more attempts available
    judge_result["revision_status"] = "needs_revision"
    return (story, judge_result, False)


def print_judge_result(judge_result: dict) -> None:
    """Format and print judge evaluation results with separate sections."""
    llm = judge_result.get("llm_judge", {})
    rule = judge_result.get("rule_check", {})

    print("\nLLM Judge Result")
    print("-" * 50)
    llm_status = "✓ PASSED" if llm.get("passes") else "✗ FAILED"
    print(f"Status: {llm_status}")
    print(f"Overall Score: {llm.get('overall_score', 0)}/10")
    print(f"  - Age Appropriateness: {llm.get('age_appropriateness', 0)}/10")
    print(f"  - Bedtime Suitability: {llm.get('bedtime_suitability', 0)}/10")
    print(f"  - Creativity: {llm.get('creativity', 0)}/10")
    print(f"  - Coherence: {llm.get('coherence', 0)}/10")

    llm_issues = llm.get("issues", [])
    if llm_issues:
        print("LLM Issues:")
        for issue in llm_issues:
            print(f"  - {issue}")

    llm_suggestions = llm.get("revision_suggestions", [])
    if llm_suggestions:
        print("LLM Suggestions:")
        for suggestion in llm_suggestions:
            print(f"  - {suggestion}")

    print("\nRule-Based Quality Check")
    print("-" * 50)
    rule_status = "✓ PASSED" if rule.get("passes") else "✗ FAILED"
    print(f"Status: {rule_status}")

    rule_blocking_issues = rule.get("blocking_issues", [])
    if rule_blocking_issues:
        print("Blocking Issues:")
        for issue in rule_blocking_issues:
            print(f"  - {issue}")

    rule_warnings = rule.get("warnings", [])
    if rule_warnings:
        print("Warnings:")
        for warning in rule_warnings:
            print(f"  - {warning}")

    rule_suggestions = rule.get("suggestions", [])
    if rule_suggestions:
        print("Suggestions:")
        for suggestion in rule_suggestions:
            print(f"  - {suggestion}")

    print("\nFinal Acceptance Result")
    print("-" * 50)
    accepted = judge_result.get("accepted", False)
    final_status = "ACCEPTED" if accepted else "NEEDS REVISION"
    print(f"Status: {final_status}")
    print(f"Revision Status: {judge_result.get('revision_status', 'needs_revision')}")
    print(f"Revision Trigger: {judge_result.get('revision_trigger', 'none')}")


def print_story_typewriter(story: str, delay: float = 0.15) -> None:
    for char in story:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    if not story.endswith("\n"):
        print()


def print_story_section(story_text: str, accepted: bool, status_text: str, use_typewriter: bool = False) -> None:
    header = "Final Story:" if accepted else "Best Available Story:"
    print(f"\n{header}")
    print("-" * 50)
    if use_typewriter:
        print_story_typewriter(story_text)
    else:
        print(story_text)
    print("-" * 50)
    print(f"\nStory Status: {status_text}")


def get_short_reason(judge_result: dict) -> str:
    rule_blocking_issues = judge_result.get("rule_check", {}).get("blocking_issues", [])
    if rule_blocking_issues:
        return str(rule_blocking_issues[0])

    llm_issues = judge_result.get("llm_judge", {}).get("issues", [])
    if llm_issues:
        return str(llm_issues[0])

    return "Story did not pass all quality checks."


def print_quality_summary(judge_result: dict) -> None:
    accepted = bool(judge_result.get("accepted", False))
    quality_status = "ACCEPTED" if accepted else "NEEDS REVISION"
    print(f"Quality Status: {quality_status}")
    if not accepted:
        print(f"Reason: {get_short_reason(judge_result)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and evaluate bedtime stories.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show full LLM judge and rule-based evaluation details.",
    )
    return parser.parse_args()


def main(debug: bool = False) -> None:
    user_request = collect_user_request()

    is_safe_request, _ = validate_initial_request(user_request)
    if not is_safe_request:
        print(UNSAFE_CHILD_STORY_MESSAGE)
        return

    story, judge_result, was_revised = generate_story_with_judge_loop(user_request, max_attempts=3)

    accepted = judge_result.get("accepted", False)
    if accepted:
        story_status = "Revised and accepted" if was_revised else "Accepted on first attempt"
    else:
        story_status = "Best draft after review, but still needs revision"

    print_story_section(story, accepted, story_status)
    print_quality_summary(judge_result)
    if debug:
        print_judge_result(judge_result)

    user_feedback = input(
        "\nWould you like to request any changes to the story? "
        "(Press Enter to keep it, or type changes like 'make it shorter', "
        "'make it funnier', 'make the ending calmer', etc.)\n"
    ).strip()

    typewriter_choice = input("Show story with typewriter animation? (Y/n): ").strip().lower()
    use_typewriter = typewriter_choice in {"", "y", "yes"}

    if not user_feedback:
        if use_typewriter:
            print_story_section(story, accepted, story_status, use_typewriter=True)
        return

    is_safe_feedback, _ = validate_user_feedback(user_feedback)
    if not is_safe_feedback:
        print(UNSAFE_CHILD_STORY_MESSAGE)
        return

    updated_story = revise_story_with_user_feedback(user_request, story, user_feedback)
    updated_judge_result = judge_story(user_request, updated_story)
    updated_judge_result["revision_status"] = (
        "accepted_after_user_feedback"
        if updated_judge_result.get("accepted", False)
        else "needs_revision_after_user_feedback"
    )
    updated_judge_result["revision_trigger"] = updated_judge_result.get("revision_trigger", "none")

    updated_accepted = updated_judge_result.get("accepted", False)
    updated_story_status = (
        "Accepted after user feedback"
        if updated_accepted
        else "Best draft after review, but still needs revision"
    )

    print_story_section(updated_story, updated_accepted, updated_story_status, use_typewriter=use_typewriter)
    print_quality_summary(updated_judge_result)
    if debug:
        print("\nUpdated Evaluation Result")
        print_judge_result(updated_judge_result)


if __name__ == "__main__":
    args = parse_args()
    main(debug=args.debug)