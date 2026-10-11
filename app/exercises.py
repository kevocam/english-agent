"""Claude crea los ejercicios en el momento y califica las respuestas."""

import random

from app import config, tutor

KEVO = (
    "The student is Kevo: Peruvian, native Spanish speaker, Senior Full Stack Developer "
    "working in Scrum teams, English level B2."
)

CONTEXTS = [
    "Agile & Scrum (daily standups, sprint planning, blockers, Kanban boards, retros)",
    "Mentorship (mentor/mentee, guidance, learning from mistakes, growth)",
    "Workplace communication (conflicts, feedback, collaboration with clients and teammates)",
]

TYPES = {
    "sentence": "Describe a specific work situation in one line and ask him to write his own sentence using the target.",
    "gap": "Give one sentence with a blank (___) where the target fits (in the right form). He must write the missing words. Don't reveal them.",
    "translate": "Give one natural Spanish sentence (neutral Latin American Spanish) that he must translate into English using the target.",
    "situation": "Describe a short workplace situation and ask one question he must answer using the target.",
    "deduction": "Give a short scenario with clear evidence and ask him to make a deduction using the target structure.",
    "connector": "Give two short related sentences and ask him to join or continue them using the target connector.",
}


def pick_type(item: dict, rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    category = item.get("category") or ""
    if category.startswith("deduction"):
        options = ["deduction", "deduction", "translate", "situation"]
    elif category.startswith("connectors"):
        options = ["connector", "connector", "translate", "sentence"]
    else:
        options = ["sentence", "gap", "translate", "situation"]
    return rng.choice(options)


def _target(item: dict) -> str:
    return (
        f"Target: {item['term']} ({item['type']})\n"
        f"Meaning: {item['definition']}\n"
        f"Example: {item.get('example') or '-'}"
    )


async def generate(item: dict, exercise_type: str, rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    system = (
        f"You write ONE short English practice exercise for a Telegram chat. {KEVO}\n\n"
        f"{_target(item)}\n\n"
        f"Exercise type: {TYPES[exercise_type]}\n"
        f"Theme: {rng.choice(CONTEXTS)}\n\n"
        "Rules: 1–3 short lines, plain text (no Markdown), start with one emoji, "
        "mention the target in bold-free plain text, never include the answer. "
        "Output only the exercise."
    )
    response = await tutor._anthropic().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": "Write the exercise."}],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()


GRADE_TOOL = {
    "name": "grade",
    "description": "Classify the student's message and, if it is an answer, grade it.",
    "input_schema": {
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["answer", "question"],
                "description": "'answer' if he is attempting the exercise (even badly, or 'I don't know'). "
                "'question' if he asks something (meaning, hint, doubt) instead of answering.",
            },
            "score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 5,
                "description": "Only for answers. 5 perfect and natural; 4 correct with a tiny issue; "
                "3 target used correctly but with grammar errors; 2 target misused or major errors; "
                "1 barely related; 0 no real attempt.",
            },
            "corrected": {
                "type": "string",
                "description": "Only for answers: a natural, corrected version of his answer. Empty if already perfect.",
            },
            "feedback": {
                "type": "string",
                "description": "For answers: 1–2 short encouraging lines explaining the main issue or what was good. "
                "For questions: a short, clear answer (you may add a hint but never give away the full solution).",
            },
        },
        "required": ["kind", "feedback"],
    },
}


async def grade(item: dict, exercise: str, answer: str) -> dict:
    system = (
        f"You are an English tutor grading one exercise in Telegram. {KEVO}\n\n"
        f"{_target(item)}\n\nExercise:\n{exercise}\n\n"
        "Judge mainly whether he used the target correctly and naturally, then overall grammar. "
        "Be encouraging but honest. Write feedback in English (a Spanish word in parentheses is fine). "
        "Plain text, no Markdown."
    )
    response = await tutor._anthropic().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=400,
        system=system,
        tools=[GRADE_TOOL],
        tool_choice={"type": "tool", "name": "grade"},
        messages=[{"role": "user", "content": answer}],
    )
    result = next(b.input for b in response.content if b.type == "tool_use")
    if result.get("kind") == "answer":
        result["score"] = max(0, min(5, int(result.get("score", 0))))
    return result
