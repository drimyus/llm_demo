import re

ALLOWED_PLATFORMS = {"Instagram", "TikTok", "UGC"}
ALLOWED_GOALS = {"Awareness", "Conversions", "Content Assets"}
ALLOWED_TONES = {"Professional", "Friendly", "Playful"}

PROFANITY_WORDS = {
    # Minimal placeholder list; extend as needed
    "fuck", "shit", "bitch", "asshole", "bastard"
}

_word_re = re.compile(r"[A-Za-z']+")

def has_profanity(text: str) -> bool:
    words = {w.lower() for w in _word_re.findall(text or '')}
    return any(w in PROFANITY_WORDS for w in words)

def validate_inputs(brand: str, platform: str, goal: str, tone: str):
    errors = {}
    if not brand or len(brand.strip()) < 2:
        errors['brand'] = 'Brand name is required.'
    if has_profanity(brand or ''):
        errors['brand'] = 'Brand name contains inappropriate language.'
    if platform not in ALLOWED_PLATFORMS:
        errors['platform'] = 'Invalid platform.'
    if goal not in ALLOWED_GOALS:
        errors['goal'] = 'Invalid goal.'
    if tone not in ALLOWED_TONES:
        errors['tone'] = 'Invalid tone.'
    return errors
