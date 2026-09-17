import os
import json
import re
from dotenv import load_dotenv
from google import genai
from models import Scenario

load_dotenv()


def get_gemini_client():
    """Create and return the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing. Add it to your .env file.")
    return genai.Client(api_key=api_key)


def generate_scenario(
    specialty: str,
    learner_level: str,
    objective: str,
    difficulty: str,
    case_type: str
) -> Scenario:
    """Generate one complete fictional clinical simulation using Gemini."""

    client = get_gemini_client()

    prompt = f"""
You are an educational clinical simulation designer.

Create ONE realistic, completely fictional clinical case for medical education.

Configuration:
- Specialty: {specialty}
- Learner level: {learner_level}
- Learning objective: {objective}
- Difficulty: {difficulty}
- Case type: {case_type}

Requirements:
- Use a NEW fictional patient name every time. Do not always use the same name.
- Generate a plausible age, gender, occupation and past medical history.
- Include chief complaint, initial presentation, vital signs and investigation results.
- Include at least 2 clinical reasoning questions.
- For every question include expected_answer and scoring_guidance.
- Include instructor_notes and hidden_diagnosis.
- Keep all details internally consistent.
- The hidden diagnosis must be supported by the case but must NOT appear in the
  student-facing chief complaint or initial presentation.
- Match the requested specialty, level, objective, difficulty and case type.
- This is a fictional educational simulation only, not real-patient advice.

Return ONLY data matching the supplied Scenario schema.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": Scenario,
            },
        )

        parsed = getattr(response, "parsed", None)
        if parsed:
            return parsed

        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini returned an empty response.")

        return Scenario.model_validate(json.loads(text))

    except Exception as e:
        raise RuntimeError(f"Failed to generate clinical scenario: {str(e)}") from e


def evaluate_student_answer(
    student_answer: str,
    expected_answer: str,
    rubric: str
) -> str:
    """
    Evaluate a student's answer.
    The response contains a machine-readable SCORE: 0-100 line so the UI
    can display the actual score instead of a hardcoded value.
    """

    client = get_gemini_client()

    prompt = f"""
You are an evaluator for a fictional medical education simulation.

Expected answer:
{expected_answer}

Scoring guidance:
{rubric}

Student answer:
{student_answer}

Evaluate ONLY the student's educational reasoning.

Give a score from 0 to 100 based on how well the student addresses the
expected reasoning and rubric. Do not give a high score merely because the
answer is long.

Return exactly this format:

SCORE: <integer 0-100>
ASSESSMENT: <one or two concise sentences>
CORRECT: <what the student did well>
MISSING: <important reasoning points that were missing or weak>
IMPROVEMENT: <one concise suggestion>

This is a fictional educational case. Do not provide personalized medical advice.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = (getattr(response, "text", "") or "").strip()

        if not text:
            raise ValueError("Gemini returned empty evaluation.")

        # Normalize score if Gemini returned an out-of-range value.
        match = re.search(r"SCORE\s*:\s*(\d{1,3})", text, re.IGNORECASE)
        if not match:
            raise ValueError("Gemini evaluation did not contain a SCORE line.")

        score = max(0, min(100, int(match.group(1))))
        text = re.sub(
            r"SCORE\s*:\s*\d{1,3}",
            f"SCORE: {score}",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        return text

    except Exception as e:
        # A local evaluation keeps the demo functional when Gemini is
        # unavailable or quota-limited.
        return _local_evaluation(student_answer, expected_answer, rubric, str(e))


def _local_evaluation(student_answer: str, expected_answer: str, rubric: str, error: str = "") -> str:
    """Deterministic local fallback evaluator used when Gemini is unavailable."""

    answer = (student_answer or "").strip()
    expected = (expected_answer or "").strip()

    if not answer:
        return (
            "SCORE: 0\n"
            "ASSESSMENT: No clinical reasoning was submitted.\n"
            "CORRECT: Nothing could be assessed.\n"
            "MISSING: A working diagnosis and supporting reasoning were not provided.\n"
            "IMPROVEMENT: State your working diagnosis and explain which case findings support it."
        )

    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "into", "would",
        "should", "could", "patient", "based", "their", "have", "has", "are",
        "was", "were", "been", "being", "what", "next", "then", "than",
        "about", "appropriate", "consider", "clinical", "case"
    }

    expected_words = {
        w.lower().strip(".,:;!?()[]{}")
        for w in re.findall(r"[A-Za-z][A-Za-z-]+", expected)
        if w.lower() not in stop_words and len(w) > 3
    }
    answer_words = {
        w.lower().strip(".,:;!?()[]{}")
        for w in re.findall(r"[A-Za-z][A-Za-z-]+", answer)
        if w.lower() not in stop_words and len(w) > 3
    }

    overlap = len(expected_words & answer_words)
    coverage = overlap / max(1, len(expected_words))

    # Reward reasoning length modestly, but do not let length dominate.
    score = round(min(100, 35 + coverage * 55 + min(len(answer_words), 80) / 80 * 10))

    if score >= 80:
        assessment = "The answer covers a strong portion of the expected reasoning."
    elif score >= 60:
        assessment = "The answer shows some relevant reasoning but several expected points are missing."
    else:
        assessment = "The answer contains limited overlap with the expected reasoning."

    correct = (
        "Several concepts in the expected answer were addressed."
        if overlap >= 3 else
        "A response was submitted, but few key expected concepts were identified."
    )
    missing = (
        "Some important case-specific reasoning or investigation points may be missing."
        if coverage < 0.75 else
        "Only minor details appear to be missing."
    )

    return (
        f"SCORE: {score}\n"
        f"ASSESSMENT: {assessment}\n"
        f"CORRECT: {correct}\n"
        f"MISSING: {missing}\n"
        "IMPROVEMENT: Link each conclusion to a specific finding from the case and explain why the next step follows."
    )
