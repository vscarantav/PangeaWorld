"""Transparent, deterministic AI-usage evidence scoring for instructors.

The score is intentionally advisory: it evaluates observable prompt habits, not
whether a student reached a particular game outcome or accepted AI advice.
"""
from collections import Counter


DEFAULT_RUBRIC = {"prompt_quality": 0.45, "usage_frequency": 0.25, "critical_thinking": 0.30}


def normalized_rubric(raw=None):
    raw = raw or {}
    rubric = {key: max(0.0, float(raw.get(key, value))) for key, value in DEFAULT_RUBRIC.items()}
    total = sum(rubric.values())
    if total <= 0:
        return dict(DEFAULT_RUBRIC)
    return {key: value / total for key, value in rubric.items()}


def grade_usage(logs, rubric=None):
    """Return an explainable 0–100 suggested score and review flags."""
    rubric = normalized_rubric(rubric)
    prompts = [str(log.prompt_text or "").strip() for log in logs]
    count = len(prompts)
    words = [prompt.split() for prompt in prompts]
    average_words = sum(len(item) for item in words) / count if count else 0
    specific = sum(1 for prompt in prompts if any(marker in prompt.lower() for marker in (
        "because", "trade-off", "alternative", "budget", "capacity", "margin", "risk", "if ", "what if")))
    quality = min(100.0, average_words * 4.0) * 0.6 + (100.0 * specific / count if count else 0.0) * 0.4
    rounds = {log.round_number for log in logs}
    frequency = min(100.0, count * 20.0) * 0.6 + min(100.0, len(rounds) * 25.0) * 0.4
    followups = sum(1 for index in range(1, count) if prompts[index - 1] and prompts[index])
    topic_terms = {term for prompt in prompts for term in ("tariff", "budget", "military", "trade", "price", "r&d", "supply", "risk", "market") if term in prompt.lower()}
    critical = (min(100.0, followups * 35.0) * 0.5) + (min(100.0, len(topic_terms) * 15.0) * 0.5)
    repeated = [prompt for prompt, occurrences in Counter(prompt.lower() for prompt in prompts if prompt).items() if occurrences > 1]
    flags = []
    if any(len(item) <= 2 for item in words): flags.append("low_effort_prompt")
    if repeated: flags.append("repeated_prompt")
    if count == 0: flags.append("no_advisor_usage")
    score = quality * rubric["prompt_quality"] + frequency * rubric["usage_frequency"] + critical * rubric["critical_thinking"]
    return {
        "suggested_score": round(score, 2), "rubric": rubric, "prompt_count": count,
        "average_prompt_words": round(average_words, 2), "rounds_used": len(rounds),
        "topic_diversity": len(topic_terms), "follow_up_depth": followups,
        "flags": flags, "components": {"prompt_quality": round(quality, 2), "usage_frequency": round(frequency, 2), "critical_thinking": round(critical, 2)},
        "instructor_override_required": True,
    }
