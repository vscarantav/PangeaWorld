"""Conservative classroom-safe validation for user-visible game names."""

import re
import unicodedata


_LEET_TRANSLATION = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})
_BLOCKED_TOKENS = {
    "asshole", "bastard", "bitch", "bullshit", "cunt", "damn", "dick", "fuck", "fucker",
    "fucking", "goddamn", "motherfucker", "nazi", "nigger", "piss", "shit", "slut", "whore",
}
_BLOCKED_PHRASES = {
    "heil hitler", "kill yourself", "white power",
}
_NAME_SUFFIXES = {"co", "corp", "inc", "kingdom", "land", "nation", "republic", "stan", "topia", "ville"}


def normalize_for_moderation(value: str) -> tuple[str, list[str]]:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    normalized = normalized.translate(_LEET_TRANSLATION)
    words = re.findall(r"[a-z]+", normalized)
    return " ".join(words), words


def is_classroom_safe_name(value: str) -> bool:
    phrase, words = normalize_for_moderation(value)
    compact = "".join(words)
    if any(blocked in phrase for blocked in _BLOCKED_PHRASES):
        return False
    if any(word in _BLOCKED_TOKENS for word in words):
        return False
    if any(word == blocked + suffix for word in words for blocked in _BLOCKED_TOKENS for suffix in _NAME_SUFFIXES):
        return False
    # Catch punctuation/spacing used to evade the filter while avoiding broad
    # substring matching that would reject innocent names such as Scunthorpe.
    return compact not in _BLOCKED_TOKENS
