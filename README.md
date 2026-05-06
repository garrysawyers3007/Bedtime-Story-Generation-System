# Bedtime Story Generation System

## 1. Project Overview
This project generates bedtime stories for children ages 5-10. It collects a story idea, child age, desired length, mood, and an optional lesson/message.

The system uses GPT-3.5-turbo to generate the story, then evaluates quality through two layers:
- an LLM judge for rubric-style scoring
- deterministic rule-based checks for product and safety guardrails

## 2. Why This Is More Than a Single Prompt
This implementation is a multi-step generation and quality loop, not a one-shot prompt:
- Collect user preferences
- Build a structured story prompt
- Generate a story draft
- Evaluate with an LLM judge
- Run deterministic rule-based quality checks
- Revise if needed
- Allow one round of user feedback/requested changes
- Re-evaluate the updated story

## 3. Key Features
- Age-aware story generation (ages 5-10)
- Age input guardrail: the CLI re-prompts until age is within 5-10 (Enter keeps default age 7)
- Length and mood control
- Optional lesson/message handling
- LLM judge for story quality
- Rule-based checks for child safety, request adherence, character agency, generic phrasing, moralizing, bedtime intensity, and age fit
- Automatic revision loop when quality gates fail
- One-round user feedback loop
- Safety handling for inappropriate requests or feedback
- Clean default output for normal users, plus optional detailed debug output for reviewers
- Optional terminal typewriter animation for story display

## 4. System Block Diagram
```text
User
   |
   v
collect_user_request()
   |
   v
validate_initial_request()
   |
   v
build_story_prompt()
   |
   v
Storyteller LLM: GPT-3.5-turbo
   |
   v
Generated Story
   |
   v
Evaluation Layer
   |-- LLM Judge
   |-- Rule-Based Checks
   |
   v
Accepted?
   | yes -> Final Story
   | no  -> build_revision_prompt() -> Revision LLM -> Re-evaluate
   |
   v
Optional User Feedback
   |
   v
validate / normalize feedback
   |
   v
revise_story_with_user_feedback()
   |
   v
Re-evaluate Updated Story
```

## 5. LLM Judge
The LLM judge evaluates:
- Age appropriateness
- Bedtime suitability
- Creativity
- Coherence
- Request adherence

The judge prompt instructs criterion-by-criterion evaluation before scoring, while requiring JSON-only output so results are easy to parse and merge into downstream decisions.

## 6. Rule-Based Checks
Deterministic checks are included because LLM judges can miss obvious product or safety issues.

Checks include:
- Unsafe or intense bedtime wording
- Missing requested elements
- Weak character agency
- Too many generic/cliche phrases
- Direct moralizing when a lesson is requested
- Stories that are too simple for ages 8-10

## 7. User Feedback Loop
After initial generation and evaluation, the user can request one round of edits, for example:
- make it shorter
- make it calmer
- make it more magical
- change the ending

Unsafe feedback is rejected. Feedback that requests unsupported or excessive length is normalized to supported bedtime-story ranges by preserving the configured short/medium/long target.

## 8. Design Choices
- All LLM calls use gpt-3.5-turbo to follow the assignment constraint.
- Different temperatures are used for generation, judging, and revision.
- Creativity is treated as sufficiently specific and not overly generic, not maximum originality.
- The system prioritizes safety, age fit, coherence, warmth, and user control.

## 9. How to Run
```bash
pip install openai
export OPENAI_API_KEY="your_key_here"
python main.py
```

Optional debug mode:

```bash
python main.py --debug
```

Output behavior:
- Default mode prints a concise summary only:
   - `Final Story:` when accepted, or `Best Available Story:` when not accepted
   - `Story Status`
   - `Quality Status: ACCEPTED` or `Quality Status: NEEDS REVISION`
   - `Reason` when not accepted (first rule-based blocking issue, otherwise first LLM issue)
- Debug mode prints the full LLM judge and rule-based breakdown using the detailed evaluation sections.
- The CLI asks `Show story with typewriter animation? (Y/n):` after the feedback prompt. This question is asked even if feedback is empty.

Do not commit your API key or any secrets to source control.

## 10. What I Would Build Next
- More automated tests for rule-based checks
- More robust story category detection
- Multi-turn feedback instead of a single feedback round
- Score tracking across revisions to quantify improvement
- A small UI for parents/children

## Sample Runs

### Example 1
Input:
- Story idea: A story about a little robot who wants to make friends.
- Age: 6
- Length: short
- Mood: calming
- Lesson: Kindness matters.

Expected behavior:
- Safe and age-appropriate
- Friendship develops through action
- May pass with creativity 7/10 because the request is simple
- Rule-based checks should pass if there is clear character agency

### Example 2
Input:
- Story idea: A story about a young inventor who builds a lantern for a sleepy village.
- Age: 9
- Length: medium
- Mood: calming
- Lesson: Small ideas can help many people.

Expected behavior:
- Slightly richer story for age 9
- Specific gentle problem
- Main character solves the problem through action
- Story may revise if it is too simple or too moralizing